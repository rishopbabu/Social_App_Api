import os
from PIL import Image
from pathlib import Path
from fastapi import HTTPException, status, APIRouter, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
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
            last_post_id = posts[-1].id
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

        response_message = "Post posted succesfully."

        return schemas.CreatePostResponse(message=response_message,
                                          post_detail=new_post)

    except Exception as e:
        error_message = "Internal Server Error: An unexpected error occurred."
        print(f'Internal Server Error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message)
