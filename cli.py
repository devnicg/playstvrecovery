from pathlib import Path
from typing import Annotated, Optional
import typer

from playstv import structured_error, get_profile, UserProfile

app = typer.Typer()


@app.command()
def main(output_path: Annotated[Optional[Path], typer.Option()]):
    if not output_path.is_dir():
        structured_error("initialization", "Specified path is not a directory")
        return

    user = typer.prompt("What's your Plays.tv username?")
    # Create UserProfile instance if archive is available
    user_profile = get_profile(user)

    # return if user profile does not exist in archive
    if user_profile is None:
        structured_error("initialization", "Could not get user profile")
        return

    # Get user id
    user_profile.get_user_id()

    # Get initial videos available from profile page
    user_profile.get_initial_videos()

    user_profile.get_more_videos()

    # Check availability of videos
    # user_profile.check_video_availability()

    # Download available user videos
    # user_profile.download_videos(output_path.name)


if __name__ == "__main__":
    app()
