from utils.helpers import owner_tag_email_regex, owner_tag_shared_regex
import re


def test_email_regex_no_match():

    # These are all 'valid' emails, so they shouldn't match
    assert not re.match(owner_tag_email_regex(), "somethingthinething@abc.com")
    assert not re.match(owner_tag_email_regex(), "a@b.c")
    assert not re.match(owner_tag_email_regex(), "@@@...")
    assert not re.match(owner_tag_email_regex(), "standard@@gmail..com")
    assert not re.match(owner_tag_email_regex(), "@.")


def test_email_regex_match():

    # These are all 'invalid' emails, so they should match
    assert re.match(owner_tag_email_regex(), "abc")
    assert re.match(owner_tag_email_regex(), "")
    assert re.match(owner_tag_email_regex(), "bob@gmailcom")
    assert re.match(owner_tag_email_regex(), "bobgmail.com")
    assert re.match(owner_tag_email_regex(), "@@@@@")
    assert re.match(owner_tag_email_regex(), ".@")


def test_shared_regex_no_match():

    # These all include 'shared', so they shouldn't match
    assert not re.match(owner_tag_shared_regex(), "shared")
    assert not re.match(owner_tag_shared_regex(), "Shared")
    assert not re.match(owner_tag_shared_regex(), "ShARed")
    assert not re.match(owner_tag_shared_regex(), "xyzsharedabc")
    assert not re.match(owner_tag_shared_regex(), "please-dont-delete-me-im-a-SHARED-resource")
    assert not re.match(owner_tag_shared_regex(), "shashashashared")
    assert not re.match(owner_tag_shared_regex(), "shared-ish")


def test_shared_regex_match():

    # These all don't include 'shared', so they should match
    assert re.match(owner_tag_shared_regex(), "share")
    assert re.match(owner_tag_shared_regex(), "shree")
    assert re.match(owner_tag_shared_regex(), "spellingshrared")
    assert re.match(owner_tag_shared_regex(), "s h a r e d")
    assert re.match(owner_tag_shared_regex(), "email@share.d")
    assert re.match(owner_tag_shared_regex(), "")