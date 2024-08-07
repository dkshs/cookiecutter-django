from __future__ import print_function

import os
import random
import shutil
import string

try:
    # Inspired by
    # https://github.com/django/django/blob/master/django/utils/crypto.py
    random = random.SystemRandom()
    using_sysrandom = True
except NotImplementedError:
    using_sysrandom = False

TERMINATOR = "\x1b[0m"
WARNING = "\x1b[1;33m [WARNING]: "
INFO = "\x1b[1;33m [INFO]: "
HINT = "\x1b[3;33m"
SUCCESS = "\x1b[1;32m [SUCCESS]: "


def remove_tailwind_files():
    file_names = [
        "tailwind.config.js",
        os.path.join("{{ cookiecutter.project_slug }}", "tailwind.css"),
    ]
    for file_name in file_names:
        os.remove(file_name)


def remove_packagejson_file():
    file_names = ["package.json"]
    for file_name in file_names:
        os.remove(file_name)


def handle_use_tailwind():
    remove_tailwind_files()
    remove_packagejson_file()


def remove_celery_files():
    file_names = [
        os.path.join("config", "celery_app.py"),
    ]
    for file_name in file_names:
        os.remove(file_name)


def handle_automated_deps_updater(option="None"):
    files_to_remove = []
    if option == "None":
        files_to_remove.extend(
            (
                os.path.join(".github", "renovate.json"),
                os.path.join(".github", "dependabot.yml"),
            )
        )
    elif option == "Renovate":
        files_to_remove.append(os.path.join(".github", "dependabot.yml"))
    elif option == "Dependabot":
        files_to_remove.append(os.path.join(".github", "renovate.json"))
    for file_name in files_to_remove:
        os.remove(file_name)


def generate_random_string(length, using_digits=False, using_ascii_letters=False, using_punctuation=False):
    """
    Example:
        opting out for 50 symbol-long, [a-z][A-Z][0-9] string
        would yield log_2((26+26+50)^50) ~= 334 bit strength.
    """
    if not using_sysrandom:
        return None

    symbols = []
    if using_digits:
        symbols += string.digits
    if using_ascii_letters:
        symbols += string.ascii_letters
    if using_punctuation:
        all_punctuation = set(string.punctuation)
        # These symbols can cause issues in environment variables
        unsuitable = {"'", '"', "\\", "$"}
        suitable = all_punctuation.difference(unsuitable)
        symbols += "".join(suitable)
    return "".join([random.choice(symbols) for _ in range(length)])


def set_flag(file_path, flag, value=None, formatted=None, *args, **kwargs):
    if value is None:
        random_string = generate_random_string(*args, **kwargs)
        if random_string is None:
            print(
                "We couldn't find a secure pseudo-random number generator on your system.",
                end=" ",
            )
            print(f"Please, make sure to manually {flag} later.")
            random_string = flag
        if formatted is not None:
            random_string = formatted.format(random_string)
        value = random_string

    with open(file_path, "r+") as f:
        file_contents = f.read().replace(flag, value)
        f.seek(0)
        f.write(file_contents)
        f.truncate()

    return value


def set_django_secret_key(file_path):
    return set_flag(
        file_path,
        "!!!SET DJANGO_SECRET_KEY!!!",
        length=64,
        using_digits=True,
        using_ascii_letters=True,
    )


def set_django_admin_url(file_path):
    return set_flag(
        file_path,
        "!!!SET DJANGO_ADMIN_URL!!!",
        formatted="{}/",
        length=32,
        using_digits=True,
        using_ascii_letters=True,
    )


def generate_random_user():
    return generate_random_string(length=32, using_ascii_letters=True)


def set_postgres_user(file_path, value):
    return set_flag(file_path, "!!!SET POSTGRES_USER!!!", value=value)


def set_postgres_password(file_path, value=None):
    return set_flag(
        file_path,
        "!!!SET POSTGRES_PASSWORD!!!",
        value=value,
        length=64,
        using_digits=True,
        using_ascii_letters=True,
    )


def set_celery_flower_user(file_path, value=None):
    return set_flag(file_path, "!!!SET CELERY_FLOWER_USER!!!", value=value)


def set_celery_flower_password(file_path, value=None):
    return set_flag(
        file_path,
        "!!!SET CELERY_FLOWER_PASSWORD!!!",
        value=value,
        length=64,
        using_digits=True,
        using_ascii_letters=True,
    )


def append_to_gitignore_file(ignored_line):
    with open(".gitignore", "a") as gitignore_file:
        gitignore_file.write(ignored_line)
        gitignore_file.write("\n")


def set_flags_in_envs(postgres_user, celery_flower_user):
    local_django_envs_path = os.path.join(".envs", ".local", ".django")
    production_django_envs_path = os.path.join(".envs", ".production", ".django")
    local_postgres_envs_path = os.path.join(".envs", ".local", ".postgres")
    production_postgres_envs_path = os.path.join(".envs", ".production", ".postgres")

    set_django_secret_key(production_django_envs_path)
    set_django_admin_url(production_django_envs_path)

    set_postgres_user(local_postgres_envs_path, value=postgres_user)
    set_postgres_password(local_postgres_envs_path)
    set_postgres_user(production_postgres_envs_path, value=postgres_user)
    set_postgres_password(production_postgres_envs_path)

    set_celery_flower_user(local_django_envs_path, value=celery_flower_user)
    set_celery_flower_password(local_django_envs_path)
    set_celery_flower_user(production_django_envs_path, value=celery_flower_user)
    set_celery_flower_password(production_django_envs_path)


def set_flags_in_settings_files():
    set_django_secret_key(os.path.join("config", "settings", "local.py"))
    set_django_secret_key(os.path.join("config", "settings", "test.py"))


def remove_celery_compose_dirs():
    shutil.rmtree(os.path.join("compose", "local", "django", "celery"))
    shutil.rmtree(os.path.join("compose", "production", "django", "celery"))


def remove_aws_dockerfile():
    shutil.rmtree(os.path.join("compose", "production", "aws"))


def remove_node_dockerfile():
    shutil.rmtree(os.path.join("compose", "local", "node"))


def remove_api_starter_files():
    os.remove(os.path.join("config", "api.py"))
    os.remove(os.path.join("tests", "test_swagger.py"))


def main():
    set_flags_in_envs(generate_random_user(), generate_random_user())
    set_flags_in_settings_files()

    append_to_gitignore_file(".env")
    append_to_gitignore_file(".envs/*")

    if "{{ cookiecutter.cloud_provider}}" != "AWS":
        remove_aws_dockerfile()

    if "{{ cookiecutter.use_tailwindcss }}".lower() == "n":
        handle_use_tailwind()
        remove_node_dockerfile()

    if "{{ cookiecutter.cloud_provider }}" == "None":
        print(
            WARNING + "You chose to not use any cloud providers nor Docker, "
            "media files won't be served in production." + TERMINATOR
        )

    if "{{ cookiecutter.use_celery }}".lower() == "n":
        remove_celery_files()
        remove_celery_compose_dirs()

    if "{{ cookiecutter.rest_framework }}" == "None":
        remove_api_starter_files()

    handle_automated_deps_updater("{{ cookiecutter.automated_deps_updater }}")

    print(f"{SUCCESS}Project initialized, keep up the good work!{TERMINATOR}")


if __name__ == "__main__":
    main()
