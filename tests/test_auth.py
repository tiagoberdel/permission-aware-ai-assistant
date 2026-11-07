from app.auth.passwords import hash_password, verify_password

def test_hash_password_result_is_string():
    password = "passwordtest"
    hashed_password = hash_password(password)

    assert isinstance(hashed_password, str)

def test_verify_correct_password():
    password = "passwordtest"
    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password) is True

def test_verify_incorrect_password():
    password = "passwordtest"
    hashed_password = hash_password(password)

    assert verify_password("wrongpassword", hashed_password) is False

def test_same_password_hashes_differ():
    password = "passwordtest"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    assert hash1 != hash2