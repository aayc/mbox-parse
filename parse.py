import mailbox
import pandas as pd
import sys
import os


def flat(ls):
    return [x for sub in ls for x in sub]


def get_charsets(msg):
    charsets = set({})
    for c in msg.get_charsets():
        if c is not None:
            charsets.update([c])
    return charsets


def handle_error(errmsg, emailmsg, cs):
    print()
    print(errmsg)
    print("This error occurred while decoding with ", cs, " charset.")
    print("These charsets were found in the one email.", get_charsets(emailmsg))


def get_body(msg):
    body = None
    # Walk through the parts of the email to find the text body.
    if msg.is_multipart():
        for part in msg.walk():

            # If part is multipart, walk through the subparts.
            if part.is_multipart():

                for subpart in part.walk():
                    if subpart.get_content_type() == "text/plain":
                        # Get the subpart payload (i.e the message body)
                        body = subpart.get_payload(decode=True)
                        # charset = subpart.get_charset()
                    else:
                        print("Found subpart:", subpart.get_content_type())

            # Part isn't multipart so get the email body
            elif part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True)
                # charset = part.get_charset()

            else:
                print("Found subpart:", subpart.get_content_type())

    # If this isn't a multi-part message then get the payload (i.e the message body)
    elif msg.get_content_type() == "text/plain":
        body = msg.get_payload(decode=True)

    # No checking done to match the charset with the correct part.
    for charset in get_charsets(msg):
        try:
            body = body.decode(charset)
        except UnicodeDecodeError:
            handle_error("UnicodeDecodeError: encountered.", msg, charset)
        except AttributeError:
            handle_error("AttributeError: encountered", msg, charset)
    return body


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise Exception(
            "Please provide the path to the mbox file, like this: python3 parse.py C:/Users/aaron/emails.mbox"
        )
    if not os.path.exists(sys.argv[1]):
        raise Exception(
            "It doesn't look like that mbox file path exists, please try a different path"
        )

    mbox_path = sys.argv[1]
    mbox = mailbox.mbox(mbox_path)
    all_ids = []
    emails = list(mbox)

    print(f"Reading and parsing ids out of {len(emails)} emails...")
    for message in emails:
        body = get_body(message)

        # Split email content into words
        words = flat(
            [lines.split(" ") for lines in body.splitlines() if lines.strip() != ""]
        )

        # Get all words that start with IMPORTANT
        ids = [word for word in words if word.startswith("IMPORTANT")]

        # Collect ids into list
        all_ids.extend(ids)

        print("STOPPING EARLY FOR TESTING PURPOSES")
        break

    # Dedup ids by converting to set (no dups) then back to list
    deduped_ids = list(set(all_ids))
    print(f"Deduplicated {len(all_ids)} ids down to {len(deduped_ids)} ids")

    # Create Pandas data frame and output to csv file
    print("Writing ids to file output_ids.csv...")
    pd.DataFrame({"id": deduped_ids}).to_csv("output_ids.csv")

    print("Done!  Have a great day!")
