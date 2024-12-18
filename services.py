import database as _database
import models as _models
import sqlalchemy.orm as _orm
import schemas as _schemas
import email_validator as _email_validator
import fastapi as _fastapi
import passlib.hash as _hash
import jwt as _jwt
import fastapi.security as _security
oauth2schema = _security.OAuth2PasswordBearer("/api/v1/user/login")
_JWT_SECRET = "lksdlkgK!#ijlkfd"


def create_db():
    return _database.Base.metadata.create_all(bind=_database.engine)


def get_db():
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


create_db()


async def getUserByEmail(email: str, db: _orm.Session):
    return db.query(_models.UserModel).filter(_models.UserModel.email == email).first()


async def create_user(user: _schemas.UserReq, db: _orm.Session):
    try:
        isValid = _email_validator.validate_email(user.email)

        email = isValid.email
    except _email_validator.EmailNotValidError:
        raise _fastapi.HTTPException(400, "Provide valid Email")

    existing_user = db.query(_models.UserModel).filter_by(email=email).first()
    if existing_user:
        raise _fastapi.HTTPException(400, "Email already exists")

    hashed_password = _hash.bcrypt.hash(user.password)
    user_obj = _models.UserModel(
        email=email,
        name=user.name,
        phone=user.phone,
        password_hash=hashed_password,
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj


async def create_token(user: _models.UserModel):
    user_schema = _schemas.UserRep.from_orm(user)
    user_dict = user_schema.dict()
    del user_dict['created_at']

    token = _jwt.encode(user_dict, _JWT_SECRET)
    return dict(access_token=token, token_type="bearer")


async def login(email: str, password: str, db: _orm.Session):
    db_user = await getUserByEmail(email=email, db=db)
    if not db_user:
        raise _fastapi.HTTPException(
            400, "This Account Isn't Register In This Site , Please First Register.")

    if not db_user.password_ver(password=password):
        raise _fastapi.HTTPException(400, "Your Password Isn't Correct!")

    return db_user


async def current_user(db: _orm.Session = _fastapi.Depends(get_db), token: str = _fastapi.Depends(oauth2schema)):
    try:
        payload = _jwt.decode(token, _JWT_SECRET, algorithms=["HS256"])
        db_user = db.query(_models.UserModel).get(payload["id"])
    except:
        raise _fastapi.HTTPException(401, "Wrong Credentials!")
    return _schemas.UserRep.from_orm(db_user)


async def create_post(user: _schemas.UserRep, db: _orm.Session, post: _schemas.PostReq):
    post = _models.PostModel(**post.dict(), user_id=user.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    # db.close()
    return _schemas.PostRes.from_orm(post)


async def get_posts_by_user(user: _schemas.UserRep, db: _orm.Session):
    posts = db.query(_models.PostModel).filter_by(user_id=user.id)
    return list(map(_schemas.PostRes.from_orm, posts))


async def get_post_detail(post_id: int, db: _orm.session):
    db_post = db.query(_models.PostModel).filter(
        _models.PostModel.id == post_id).first()
    if not db_post:
        raise _fastapi.HTTPException(404, "Post Not Found")
    return db_post


async def delete_post(post_id: int, user_id: int, db: _orm.Session):
    db_post = db.query(_models.PostModel).filter(
        _models.PostModel.id == post_id,
        _models.PostModel.user_id == user_id
    ).first()

    if not db_post:
        raise _fastapi.HTTPException(
            404, "Post not found or you don't have permission to delete")

    db.delete(db_post)
    db.commit()
    return True


async def update_post(post_req: _schemas.PostReq, post: _models.PostModel, db: _orm.Session):
    post.post_title = post_req.post_title
    post.post_description = post_req.post_description
    post.image = post_req.image

    db.commit()
    db.refresh(post)

    return _schemas.PostRes.model_validate(post)


async def get_all_posts(db: _orm.Session):
    posts = db.query(_models.PostModel)
    return list(map(_schemas.PostRes.from_orm, posts))


async def get_user_details(user_id: int, db: _orm.session):
    db_user = db.query(_models.UserModel).filter(
        _models.UserModel.id == user_id).first()
    if not db_user:
        raise _fastapi.HTTPException(404, "user Not Found")
    return db_user
