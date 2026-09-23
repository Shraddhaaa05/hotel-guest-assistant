from app.services.intent import Intent, classify_intent, extract_availability_params


def test_classifies_explicit_availability_keyword():
    assert classify_intent("Do you have any rooms available?") == Intent.AVAILABILITY


def test_classifies_date_containing_message_as_availability():
    assert classify_intent("Rooms for 2026-10-10 to 2026-10-12?") == Intent.AVAILABILITY


def test_classifies_plain_faq_question_as_knowledge():
    assert classify_intent("What time is check-in?") == Intent.KNOWLEDGE


def test_classifies_amenity_question_as_knowledge():
    assert classify_intent("Does the hotel have a pool?") == Intent.KNOWLEDGE


def test_extracts_full_availability_params():
    check_in, check_out, guests = extract_availability_params(
        "Do you have rooms for 3 guests from 2026-10-10 to 2026-10-12?"
    )
    assert check_in == "2026-10-10"
    assert check_out == "2026-10-12"
    assert guests == 3


def test_extracts_partial_params_when_some_missing():
    check_in, check_out, guests = extract_availability_params("Is there any availability?")
    assert check_in is None
    assert check_out is None
    assert guests is None
