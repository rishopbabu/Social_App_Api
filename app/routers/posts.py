import base64
import os
from PIL import Image
from pathlib import Path
from fastapi import HTTPException, status, APIRouter, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..databases import get_db
from .. import models, oauth2, schemas

router = APIRouter(prefix="/post", tags=["Posts"])

# Specify the directory path
post_images_directory = "posts_images"

if not os.path.exists(post_images_directory):
    os.makedirs(post_images_directory)

router.mount("/posts_images",
             StaticFiles(directory="posts_images"),
             name="posts_images")

#CRUD Operations


# Create a new post
@router.post("/create_post",
             name="Create a new post",
             status_code=status.HTTP_201_CREATED)
async def create_post(post: schemas.CreatePost = Depends(
    schemas.CreatePost.as_form),
                      image: UploadFile = File(...),
                      db: Session = Depends(get_db),
                      current_user: int = Depends(oauth2.get_current_user)):

    try:
        user = db.query(
            models.Users).filter(models.Users.id == current_user.id).first()
        user_id = user.id

        posts = db.query(models.Post).all()

        if posts:
            last_post_id = posts[-1].post_id
            next_post_id = last_post_id + 1

        else:
            last_post_id = None
            next_post_id = 1

        allowed_formats = ["jpeg", "jpg", "png", "heic"]
        file_extension = image.filename.split(".")[-1].lower()

        if file_extension not in allowed_formats:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid file format")

        # Save the image to the server
        image_path = os.path.join("posts_images",
                                  f"{next_post_id}_{user_id}_post.jpg")
        with open(image_path, "wb") as image_file:
            image_file.write(await image.read())

        # Optionally, convert HEIC to JPEG (requires Pillow library)
        if file_extension == "heic":
            img = Image.open(image_path)
            img = img.convert("RGB")
            img.save(image_path.replace("heic", "jpg", "png"), "JPEG")
            os.remove(image_path)  # Remove the original HEIC file

        new_post = models.Post(user_id=user_id,
                               post_image=image_path,
                               **post.model_dump())

        db.add(new_post)
        db.commit()
        db.refresh(new_post)

        new_post_response = schemas.PostResponseBase.from_db(new_post)

        vote_count = 0

        response_message = "Post posted succesfully."

        response_model = schemas.PostResponseBase(
            post_id=new_post_response.post_id,
            user_id=new_post_response.user_id,
            caption=new_post_response.caption,
            is_published=new_post_response.is_published,
            post_image=new_post_response.post_image,
            updated_by=new_post_response.updated_by,
            user_detail=new_post_response.user_detail,
            votes=vote_count)

        return schemas.CreatePostResponse(message=response_message,
                                          post_detail=response_model,
                                          votes=vote_count)

    # Re-raise the HTTP exception
    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        error_message = "Internal Server Error: An unexpected error occurred."
        print(f'Internal Server Error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message)

# Function to encode an image to base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read())
    return encoded_image.decode("utf-8")


# Get all the posts
@router.get("/get_all_post",
            name="Get All the posts",
            status_code=status.HTTP_200_OK)
async def get_all_posts(db: Session = Depends(get_db),
                        current_user: int = Depends(oauth2.get_current_user)):

    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="You are not authorised to use this.")

        posts_with_votes = (db.query(
            models.Post,
            func.count(models.Votes.post_id).label("votes")).outerjoin(
                models.Votes,
                models.Votes.post_id == models.Post.post_id).group_by(
                    models.Post.post_id).all())

        response_message = "All posts fetched successfully."

        total_posts = len(posts_with_votes)

        post_response = [
            schemas.PostResponseBase(
                post_id=post.post_id,  # Use 'post' instead of 'posts' here
                user_id=post.user_id,
                caption=post.caption,
                is_published=post.is_published,
                post_image=encode_image_to_base64(post.post_image),
                updated_by=post.updated_by,
                user_detail=schemas.UserDetail.from_users_model(
                    post.user_detail),
                votes=votes if votes else 0,
                profile_picture_base64=encode_image_to_base64(post.user_detail.profile_pic))
            for (post, votes
                 ) in posts_with_votes  # Use 'votes' instead of 'posts' here
        ]

        response_model = schemas.GetPostsResponse(message=response_message,
                                                  total_posts=total_posts,
                                                  post_details=post_response)

        return response_model

    # Re-raise the HTTP exception
    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        error_message = "Internal Server Error: An unexpected error occurred."
        print(f'Internal Server Error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message)


# Get an individual post by id
@router.get("/get_post/{post_id}",
            name="Get post by ID",
            status_code=status.HTTP_200_OK)
async def get_user_by_id(post_id: int,
                         db: Session = Depends(get_db),
                         current_user: int = Depends(oauth2.get_current_user)):

    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="You are not authorised to use this.")

        post = db.query(
            models.Post).filter(models.Post.post_id == post_id).first()

        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Post with id: {post_id} not found.')

        response_message = "Post fetched successfully."

        post_response = schemas.PostResponseBase.from_db(post)

        response_model = schemas.GetIndividualPostResponse(
            message=response_message, post_detail=post_response)

        return response_model

    # Re-raise the HTTP exception
    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        error_message = "Internal Server Error: An unexpected error occurred."
        print(f'Internal Server Error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message)


# Update a post:
@router.put("/update_post/{post_id}",
            name="Update post by id",
            status_code=status.HTTP_200_OK)
async def update_post(post_id: int,
                      update_post: schemas.CreatePost,
                      db: Session = Depends(get_db),
                      current_user: int = Depends(oauth2.get_current_user)):

    try:
        post_query = db.query(
            models.Post).filter(models.Post.post_id == post_id)

        post = post_query.first()

        if post == None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Post with id: {post_id} does not exits.')

        if post.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f'Not authorized to do this action.')

        post_query.update(update_post.model_dump(), synchronize_session=False)

        db.commit()

        update_post = post_query.first()

        update_post_response = schemas.PostResponseBase.from_db(update_post)

        vote_count = 0

        response_message = "Post posted succesfully."

        response_model = schemas.PostResponseBase(
            post_id=update_post_response.post_id,
            user_id=update_post_response.user_id,
            caption=update_post_response.caption,
            is_published=update_post_response.is_published,
            post_image=update_post_response.post_image,
            updated_by=update_post_response.updated_by,
            user_detail=update_post_response.user_detail,
            votes=vote_count)

        return schemas.CreatePostResponse(message=response_message,
                                          post_detail=response_model,
                                          votes=vote_count)

    # Re-raise the HTTP exception
    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        error_message = "Internal Server Error: An unexpected error occurred."
        print(f'Internal Server Error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message)


# Delete post by ID
@router.delete("/delete_post/{post_id}",
               name="Delete a post by ID",
               status_code=status.HTTP_200_OK)
async def delete_post(post_id: int,
                      db: Session = Depends(get_db),
                      current_user: int = Depends(oauth2.get_current_user)):

    try:
        post_query = db.query(
            models.Post).filter(models.Post.post_id == post_id)

        post = post_query.first()

        if post == None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'post with id: {post_id} does not exists.')

        if post.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to perform this action.")

        if post.post_image:
            delete_file_in_path(post.post_image)

        post_query.delete(synchronize_session=False)
        db.commit()

        response_message = "Post deleted successfully."

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
