import base64
import io
from fastapi import HTTPException, APIRouter, status, Depends, Query, Body, UploadFile, File, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session, load_only
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from PIL import Image
from io import BytesIO
from sqlalchemy import asc
import os
from pathlib import Path
from ..databases import get_db
from .. import models, schemas, utils, oauth2, databases

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Specify the directory path
profile_pictures_directory = "profile_pictures"

if not os.path.exists(profile_pictures_directory):
    os.makedirs(profile_pictures_directory)

router.mount("/profile_pictures",
             StaticFiles(directory="profile_pictures"),
             name="profile_pictures")


# Create a new user
@router.post("/register",
             name="Create User Account",
             status_code=status.HTTP_201_CREATED)
async def register(user: schemas.RegisterUser, db: Session = Depends(get_db)):

    try:
        # Validate required fields
        if not all([
                user.first_name, user.last_name, user.phone, user.email,
                user.password
        ]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="All fields are required.")

        # Check if the user's email or phone already exists
        existing_user_email = (db.query(
            models.Users).filter(models.Users.email == user.email).first())
        existing_user_phone = (db.query(
            models.Users).filter(models.Users.phone == user.phone).first())

        if existing_user_email and existing_user_phone:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=
                f"User with email: {user.email} & phone: {user.phone} already exists.",
            )
        elif existing_user_email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"User with email: {user.email} already exists.",
            )
        elif existing_user_phone:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"User with phone: {user.phone} already exists.",
            )

        # Hash the password and store
        hashed_pwd = utils.hash_password(user.password)
        user.password = hashed_pwd

        new_user = models.Users(**user.model_dump())

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create a UserDetail instance from the Users model
        user_detail = schemas.UserDetail.from_users_model(new_user)

        response_message = "User creation was successful."

        response_model = schemas.RegisterUserResponse(message=response_message,
                                                      user_detail=user_detail)

        return response_model

    # Re-raise the HTTP exception
    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        error_message = "Internal Server Error: An unexpected error occurred."
        print(f'Internal Server Error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message)


# Login User
@router.post("/login", name="User Login", status_code=status.HTTP_200_OK)
async def login_user(user_credentials: OAuth2PasswordRequestForm = Depends(),
                     db: Session = Depends(databases.get_db)):

    try:
        user = db.query(models.Users).filter(
            models.Users.email == user_credentials.username).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Invalid username or password")

        if not utils.verify_password(user_credentials.password, user.password):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Invalid username or password")

        user_detail = schemas.UserLogin.from_db(user)

        access_token = oauth2.create_access_token(data={"user_id": user.id})

        response_model = schemas.UserLoginResponse(message="Login Successful",
                                                   access_token=access_token,
                                                   token_type="Bearer",
                                                   user_detail=user_detail)

        return response_model

    # Re-raise the HTTP exception
    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        error_message = "Internal Server Error: An unexpected error occurred."
        print(f'Internal Server Error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message)


# Get All Users
@router.get("/get_all_users",
            name="Get All the users",
            status_code=status.HTTP_200_OK)
async def get_all_users(skip: int = Query(0, description="Skip this many records", ge=0),
    limit: int = Query(0, description="Limit the number of records", le=0),
        db: Session = Depends(get_db),
        current_user: int = (Depends(oauth2.get_current_user))):
    try:
        query = db.query(models.Users).options(
            load_only(models.Users.id, models.Users.first_name,
                      models.Users.last_name, models.Users.phone,
                      models.Users.profile_pic, models.Users.email,
                      models.Users.updated_by))

        query = query.order_by(asc(models.Users.id))

        if not skip and not limit:
            users = query.all()

        elif skip:
            users = query.offset(skip).all()

        elif limit:
            users = query.limit(limit).all()

        else:
            users = query.offset(skip).limit(limit).all()

        if not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorised to do get all users.")

        response_message = "All users data Fetched Successfully."
                
        user_details = []
        for user in users:
           
            profile_pic_path = f"profile_pictures/{user.id}.jpg"
            
            if os.path.isfile(profile_pic_path):
                with open(profile_pic_path, "rb") as image_file:
                    encoded_profile_pic = base64.b64encode(image_file.read()).decode("utf-8")
            else:
                # Set a default or placeholder image if no image is available
                encoded_profile_pic = None
            
            user_detail = schemas.UserDetail(id=user.id,
                                             first_name=user.first_name,
                                             last_name=user.last_name,
                                             phone=user.phone,
                                             email=user.email,
                                             profile_pic=encoded_profile_pic,
                                             updated_by=user.updated_by)
            user_details.append(user_detail)
       
        total_users_count = len(user_details)
        
        response_model = schemas.UserListResponse(message=response_message,
                                                  total_users_count=total_users_count,
                                                  users_list=user_details)
        
        return response_model        

    # Re-raise the HTTP exception
    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        error_message = "Internal Server Error: An unexpected error occurred."
        print(f'Internal Server Error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message)


# Get users by id
@router.get("/get_user/{id}",
            name="Get users by ID",
            status_code=status.HTTP_200_OK)
async def get_user_by_id(id: int,
                         db: Session = Depends(get_db),
                         current_user: int = Depends(oauth2.get_current_user)):

    user = db.query(models.Users).filter(models.Users.id == id).first()
    print("users:", user)
    try:
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id: {id} does not exists",
            )

        if not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorised to do get all users.")

        response_message = "User data Fetched Successfully."

        user_detail = schemas.UserDetail.from_users_model(user)

        response_model = schemas.GetUsersByIDResponse(message=response_message,
                                                      user_detail=user_detail)

        return response_model

    # Re-raise the HTTP exception
    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        error_message = "Internal Server Error: An unexpected error occurred."
        print(f'Internal Server Error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message)


# Update user by id
# The update_user should be send in body as raw json format
@router.put(
    "/update_user/{id}",
    name="Update user profile detals",
    status_code=status.HTTP_200_OK,
)
async def update_user(id: int,
                      update_user: schemas.UpdateUserDetail = Body(...),
                      db: Session = Depends(get_db),
                      current_user: int = Depends(oauth2.get_current_user)):

    try:
        if current_user.id != id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail='Access not granted to do this action')

        existing_user_email = db.query(models.Users).filter(
            models.Users.id != id,
            models.Users.email == update_user.email).first()

        existing_user_phone = db.query(models.Users).filter(
            models.Users.id != id,
            models.Users.phone == update_user.phone).first()

        if existing_user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Email {update_user.email} already exists.')

        if existing_user_phone:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Phone {update_user.phone} already exists.')

        user = db.query(models.Users).filter(models.Users.id == id).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f'User with id: {id} does not exists.')

        if update_user.first_name:
            user.first_name = update_user.first_name

        if update_user.last_name:
            user.last_name = update_user.last_name

        if update_user.email:
            user.email = update_user.email

        if update_user.phone:
            user.phone = update_user.phone

        db.commit()

        updated_user = db.query(
            models.Users).filter(models.Users.id == id).first()

        updated_user_detail = schemas.UserDetail.from_users_model(updated_user)

        response_mesage = "Details updated successfully."

        response_model = schemas.UpdateUserDetailResponse(
            message=response_mesage, user_detail=updated_user_detail)

        return response_model

    # Re-raise the HTTP exception
    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        error_message = "Internal Server Error: An unexpected error occurred."
        print(f'Internal Server Error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message)


# Update Password
# The password should be send in body as raw json format
@router.put("/update_password/{id}",
            name="Update or change password",
            status_code=status.HTTP_200_OK)
async def update_password(id: int,
                          new_password: schemas.UpdatePassword = Body(...),
                          db: Session = Depends(get_db),
                          current_user: int = Depends(
                              oauth2.get_current_user)):

    try:
        user_query = db.query(models.Users).filter(models.Users.id == id)

        user = user_query.first()

        if current_user.id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Not authorized to do this action.")

        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"User with id {id} does not exist.")

        password = new_password.password

        hashed_pwd = utils.hash_password(password)

        user.password = hashed_pwd

        print('hashed_pwd', hashed_pwd)

        db.commit()

        response_mesage = "Password updated successfully."

        response_model = schemas.CommonMessageResponse(message=response_mesage)

        return response_model

    # Re-raise the HTTP exception
    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        error_message = "Internal Server Error: An unexpected error occurred."
        print(f'Internal Server Error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message)


# Upload Profile Picture
@router.post("/upload_profile_pic/{id}",
             name="Upload your profile picture",
             status_code=status.HTTP_200_OK)
async def upload_profile_pic(id: int,
                             profile_pic: UploadFile = File(...),
                             db: Session = Depends(get_db),
                             current_user: str = Depends(
                                 oauth2.get_current_user)):

    try:
        user = db.query(models.Users).filter(models.Users.id == id).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="User not found")

        if user.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Not authorized.")

        allowed_formats = ["jpeg", "jpg", "png", "heic"]
        file_extension = profile_pic.filename.split(".")[-1].lower()

        if file_extension not in allowed_formats:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid file format")

        file_path = f'profile_pictures/{user.id}.jpg'

        # Check if the file already exists and remove it
        if os.path.exists(file_path):
            os.remove(file_path)

        with open(file_path, "wb") as f:
            f.write(await profile_pic.read())

        # Optionally, convert HEIC to JPEG (requires Pillow library)
        if file_extension == "heic":
            img = Image.open(file_path)
            img = img.convert("RGB")
            img.save(file_path.replace("heic", "jpg", "png"), "JPEG")
            os.remove(file_path)  # Remove the original HEIC file

        user.profile_pic = file_path

        db.commit()

        response_message = "Profile picture uploaded successfully"

        response_model = schemas.UpdateProfileResponse(
            message=response_message,
            user_detail=schemas.UserDetailAfterProfileUpdate.from_users_model(
                user))

        return response_model

    # Re-raise the HTTP exception
    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal server error.")


# Get profile pictures
@router.get("/get_profile_picture_url/{id}",
            name="Get profile picture URL",
            status_code=status.HTTP_200_OK)
async def get_profile_picture_url(id: int,
                                  db: Session = Depends(get_db),
                                  current_user: str = Depends(
                                      oauth2.get_current_user)):
    user = db.query(models.Users).filter(models.Users.id == id).first()

    if current_user.id != id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authorized.")

    if not user or not user.profile_pic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User or profile picture not found")

    # Construct the file path to the user's profile picture
    file_path = f"profile_pictures/{user.id}.jpg"

    try:
        # Check if the file exists
        if not Path(file_path).is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Profile picture file not found")

        return FileResponse(file_path, media_type="image/jpeg")

    # Re-raise the HTTP exception
    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        error_message = "Internal Server Error: An unexpected error occurred."
        print(f'Internal Server Error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message)


# Delete user by id
@router.delete("/delete_user/{id}",
               name="Delete user account",
               status_code=status.HTTP_200_OK)
async def delete_user(id: int,
                      db: Session = Depends(get_db),
                      current_user: str = Depends(oauth2.get_current_user)):
    try:
        if current_user.id != id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail='Access not granted to do this action')

        user_query = db.query(models.Users).filter(models.Users.id == id)
        user = user_query.first()

        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f'User with id: {id} does not exists.')

        posts = db.query(models.Post).filter(models.Post.user_id == id).all()

        for post in posts:
            if post.post_image:
                delete_file_in_path(post.post_image)

        if user.profile_pic:
            delete_file_in_path(user.profile_pic)

        user_query.delete(synchronize_session=False)

        db.commit()

        response_message = "User deleted successfully."

        return schemas.CommonMessageResponse(message=response_message)

    # Re-raise the HTTP exception
    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        error_message = "Internal Server Error: An unexpected error occurred."
        print(f'Internal Server Error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message)


def delete_file_in_path(file_path):
    try:
        # Check if the file exists
        if os.path.exists(file_path):
            print(f"Deleting file: {file_path}")
            # Split the file path to get the directory and file name
            directory, file_name = os.path.split(file_path)

            # Delete the file without removing the directory
            os.remove(os.path.join(directory, file_name))
        else:
            print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error deleting file: {str(e)}")
