import uuid
from app.db import engine, Base
from binascii import Error
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.UsersModel import User, PasswordResetToken, Group, UsersGroups
from app.shema import RegisterUser, ShowUser, LoginUser, UpdateUser, CreateGroup, ShowGroup, UpdateGroup
from fastapi import HTTPException, status
from app.db import get_session
from app.config import config
from app.utillits import create_access_token, hash_password, check_password
from app.utillits import create_refresh_token, hash_refresh_token, decode_refresh_token
from app.get_current_user import get_current_user
from app.celery_app import send_email
from app.shema import PasswordResetRequest, PasswordResetConfirm
from app.models.UsersModel import PasswordResetToken
from app.models.TokenModel import RefreshToken


app = FastAPI(
    title="User service",
    version="1.0.0",
    root_path="/users"
)

# Создаём базу данных
@app.get("/init")
async def create_db():
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except Error as e:
            print(e)     
        await  conn.run_sync(Base.metadata.create_all)
    return({"msg":"db creat! =)"})

subject = "Регистрация на сайте QRCard"
text = """
Здравствуйте!

Спасибо, что зарегистрировались на нашем сайте.

Теперь Вы можете создавать интерактивные викторины и тесты.

Надеемся, что наш сервис будет полезен Вам в вашей работе 
и поможет сделать обучение более интересным и эффективным.

С уважением, администрация сайта QRCard.
"""

#################################Работа с  пользователями##############################################
# Регистрация пользователя с отправкой сообщения на email
@app.post("/register")
async def register_user(data:RegisterUser, session:AsyncSession = Depends(get_session)):
    
    isUserEx = await session.scalar(select(User).where(User.email == data.email))
    
    if isUserEx:
        raise HTTPException(status_code=411, detail={
        "status":411,
        "data":"user is exists"
        })
        
    data_dict = data.model_dump()
        
    data_dict["password"] = await hash_password(password=data.password)
    
    user = User(**data_dict)
    session.add(user) 
    await session.flush([user])

    user_id = user.id
        
    await session.commit()
    send_email.delay(user.email, subject, text)
        
    user_token = create_access_token(user_id=user_id)
    data_dict["token"] = user_token  
        
    return data_dict

# Авторизация пользователя
@app.post("/login")
async def login(
    data: LoginUser,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(User).where(User.email == data.email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not await check_password(user.password, data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    refresh_db = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.utcnow()
        + timedelta(days=config.auth_data.days)
    )
    session.add(refresh_db)
    await session.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# Получение пользователя
@app.get("/me", response_model=ShowUser)
async def me(me = Depends(get_current_user)):
     return me

# Изменение данных пользователя
@app.put("/update", response_model=ShowUser)
async def update_user(data: UpdateUser, 
                      me = Depends(get_current_user),
                      session: AsyncSession = Depends(get_session)):
    await session.refresh(me)
    if data.name:
        me.name = data.name
    if data.surname:
        me.surname = data.surname
    if data.dob:
        me.dob = data.dob
    if data.role:
        me.role = data.role
    if data.groups:
        me.groups = data.groups

    await session.commit()
    await session.refresh(me)
    
    return me

# Удаление пользователя
@app.delete("/delete/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Проверка, что текущий пользователь — админ
    if current_user.role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете прав на удаление пользователя."
        )
    user = await session.scalar(select(User).where(User.id == user_id))
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(user)
    await session.commit()

    return {"message": f"User with ID {user_id} has been deleted"}

#################################Работа с токенами##############################################
# Рефреш токен
@app.post("/refresh")
async def refresh(
    refresh_token: str,
    session: AsyncSession = Depends(get_session)
):
    payload = decode_refresh_token(refresh_token)

    token_hash = hash_refresh_token(refresh_token)

    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False
    )
    result = await session.execute(stmt)
    token_db = result.scalar_one_or_none()

    if not token_db:
        raise HTTPException(status_code=401, detail="Token revoked")

    # revoke old refresh
    token_db.revoked = True

    # create new tokens
    user_id = uuid.UUID(payload["sub"])
    new_access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id)

    session.add(
        RefreshToken(
            user_id=user_id,
            token_hash=hash_refresh_token(new_refresh),
            expires_at=datetime.utcnow()
            + timedelta(days=config.auth_data.days)
        )
    )

    await session.commit()

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }


# Запрос на восстановление пароля
@app.post("/password-reset")
async def password_reset_request(
    data: PasswordResetRequest,
    session: AsyncSession = Depends(get_session)
):
    user = await session.scalar(
        select(User).where(User.email == data.email)
    )

    #не раскрываем, существует ли пользователь
    if not user:
        return {"status": "ok"}

    token = str(uuid.uuid4())

    reset_token = PasswordResetToken(
        token=token,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )

    session.add(reset_token)
    await session.commit()

    reset_link = f"https://your-frontend/reset-password?token={token}"

    send_email.delay(
        user.email,
        "Восстановление пароля",
        f"Перейдите по ссылке для восстановления пароля:\n{reset_link}"
    )

    return {"status": "ok"}


# Подтверждение и смена пароля
@app.post("/password-reset/confirm")
async def password_reset_confirm(
    data: PasswordResetConfirm,
    session: AsyncSession = Depends(get_session)
):
    token_obj = await session.scalar(
        select(PasswordResetToken)
        .where(PasswordResetToken.token == data.token)
    )

    if not token_obj or token_obj.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = await session.get(User, token_obj.user_id)

    user.password = await hash_password(data.new_password)

    await session.execute(
        delete(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id
        )
    )

    await session.commit()

    return {"status": "password updated"}


@app.post("/logout")
async def logout(
    refresh_token: str,
    session: AsyncSession = Depends(get_session)
):
    token_hash = hash_refresh_token(refresh_token)

    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False
    )
    result = await session.execute(stmt)
    token_db = result.scalar_one_or_none()

    if not token_db:
        raise HTTPException(status_code=401, detail="Invalid token")

    token_db.revoked = True
    await session.commit()

    return {"detail": "Logged out successfully"}

#################################Работа с группами##############################################
# Создание группы
@app.post("/groups/create", response_model=ShowGroup)
async def create_group(data: CreateGroup, 
                    current_user = Depends(get_current_user), 
                       session: AsyncSession = Depends(get_session)):
    # Проверка, что текущий пользователь — учитель или админ
    if current_user.role.value != "ADMIN" and current_user.role.value != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеетe прав на создание группы."
        )
    newGroup = Group(**data.model_dump(), user_id=current_user.id)
    session.add(newGroup)
    await session.commit()
    await session.refresh(newGroup)
    
    return newGroup

# Получение группы по ID
@app.get("/groups/{group_id}", response_model=ShowGroup)
async def get_group(
    group_id: uuid.UUID,
    session: AsyncSession = Depends(get_session)
):
    group = await session.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    return group

# получение списка всех групп
@app.get("/groups")
async def get_groups(
    current_user: User = Depends(get_current_user),
    session:AsyncSession = Depends(get_session)
    ):
    if current_user.role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете прав на просмотр групп."
        )
    profiles = await session.scalars(select(Group))
    return profiles.all()

# Редактирование названия группы
@app.put("/groups/{group_id}")
async def update_group_name(group_id: uuid.UUID, 
                            data: UpdateGroup, 
                            session: AsyncSession = Depends(get_session)):
    group = await session.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group.name_group = data.name_group
    await session.commit()
    await session.refresh(group)

    return {"detail": f"Group {group_id} name updated", 
            "group": {"id": group.id, "name_group": group.name_group}}

@app.delete("/groups/{group_id}")
async def delete_group(group_id: uuid.UUID,
                       session: AsyncSession = Depends(get_session)):
    group = await session.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    await session.delete(group)
    await session.commit()

    return {"detail": f"Group {group_id} deleted"}

####################################Работа с пользователями в группах##############################################
# Добавление пользователя в группу
@app.post("/groups/{group_id}/add_user/{user_id}")
async def add_user_to_group(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if current_user.role.value != "ADMIN" and current_user.role.value != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете прав на добавление пользователя в группу."
        )   
    group = await session.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    user = await session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_user_in_group = await session.scalar(
        select(UsersGroups).where(
            UsersGroups.group_id == group_id,
            UsersGroups.user_id == user_id
        )
    )
    if is_user_in_group:
        raise HTTPException(status_code=409, detail="User already in group")

    session.add(UsersGroups(group_id=group_id, user_id=user_id))
    await session.commit()

    return {"detail": f"User {user_id} added to group {group_id}"}

# Получение всех групп пользователя
@app.get("/users/{user_id}/groups", response_model=list[ShowGroup])
async def get_user_groups(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    stmt = select(Group).where(Group.user_id == current_user.id)
    result = await session.execute(stmt)
    groups = result.scalars().all()
    return groups

# Получение всех пользователей в группе
@app.get("/groups/{group_id}/users", response_model=list[ShowUser])
async def get_group_users(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if current_user.role.value != "ADMIN" and current_user.role.value != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете прав на просмотр пользователей в группе."
        )
    group = await session.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    stmt = (
        select(User)
        .options(selectinload(User.groups))
        .join(UsersGroups)
        .where(UsersGroups.group_id == group_id)
    )
    result = await session.execute(stmt)
    users = result.scalars().all()
    return users

# Удаление пользователя из группы
@app.delete("/groups/{group_id}/remove_user/{user_id}")
async def remove_user_from_group(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if current_user.role.value != "ADMIN" and current_user.role.value != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не имеете прав на удаление пользователя из группы."
        )
    group = await session.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    user = await session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_user_in_group = await session.scalar(
        select(UsersGroups).where(
            UsersGroups.group_id == group_id,
            UsersGroups.user_id == user_id
        )
    )
    if not is_user_in_group:
        raise HTTPException(status_code=404, detail="User not in group")

    await session.delete(is_user_in_group)
    await session.commit()

    return {"detail": f"User {user_id} removed from group {group_id}"}
