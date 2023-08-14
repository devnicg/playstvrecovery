from playstvrecovery.playstv import UserProfile


test_username = "MrNicola"
test_user_profile = UserProfile(test_username)


def test_userprofile_init():
    test_user_profile = UserProfile(test_username)

    assert test_user_profile.username == test_username
    assert test_user_profile.original_url == f"https://plays.tv/u/{test_username}"


def test_userprofile_availability_check():
    available = test_user_profile.check_availability()

    if available:
        assert len(test_user_profile.archive_url) > 0
    else:
        assert len(test_user_profile.archive_url) < 1


def test_userprofile_get_user_id():
    test_user_profile.check_availability()
    if test_user_profile.archive_url:
        test_user_profile.get_user_id()
        assert len(test_user_profile.__user_id__) > 0
    else:
        assert False
