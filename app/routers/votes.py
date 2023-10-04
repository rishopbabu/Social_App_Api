from fastapi import Depends, status, HTTPException, APIRouter
from sqlalchemy.orm import Session
from .. import (models, schemas, oauth2, databases)
from typing import List

router = APIRouter(prefix="/vote", tags=["Votes"])


@router.post("/post_vote",
             name="Give vote to post",
             status_code=status.HTTP_200_OK)
async def post_vote(vote: schemas.Vote,
                    db: Session = Depends(databases.get_db),
                    current_user: int = Depends(oauth2.get_current_user)):

    try:
        post = db.query(
            models.Post).filter(models.Post.post_id == vote.post_id).first()

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The post: {vote.post_id} does not exists.")

        vote_query = db.query(models.Votes).filter(
            models.Votes.post_id == vote.post_id,
            models.Votes.user_id == current_user.id)

        found_vote = vote_query.first()

        if vote.dir == 1:
            if found_vote:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=
                    f'User {current_user.id} has already voted on this post {vote.post_id}'
                )

            new_vote = models.Votes(post_id=vote.post_id,
                                    user_id=current_user.id)
            db.add(new_vote)
            db.commit()
            db.refresh(new_vote)

            response_message_vote = "Vote posted successully."

            response_vote = vote

            response_model = schemas.VoteResponse(
                message=response_message_vote, vote=response_vote)

            return response_model

        else:
            if not found_vote:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail="Vote dosen't exists")

            vote_query.delete(synchronize_session=False)
            db.commit()

            response_message_delete = "Vote deleted successfully."

            response_vote = vote

            response_model = schemas.VoteResponse(
                message=response_message_delete, vote=response_vote)

            return response_model

    # Re-raise the HTTP exception
    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        error_message = "Internal Server Error: An unexpected error occurred."
        print(f'Internal Server Error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_message)
