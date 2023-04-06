import os
from datetime import datetime, timezone, timedelta

import pygit2 as git
from pygit2._pygit2 import GitError, GIT_SORT_TIME, GIT_SORT_REVERSE

# Format: Fri Sep  2 19:36:07 2022 +0530
GIT_TIME_FORMAT = "%c %z"


def getLastModifiedStr(date):
    """
    Returns last modified string
    date: offset-aware datetime.datetime object
    """

    # Get time difference
    now = datetime.now(timezone.utc)
    delta = now - date

    output = ""

    days = delta.days
    if days <= 0:
        hours = delta.seconds // 3600
        if hours <= 0:
            mins = (delta.seconds // 60) % 60
            if mins <= 0:
                secs = delta.seconds - hours * 3600 - mins * 60
                if secs <= 0:
                    output = "now"

                # Secs
                elif secs == 1:
                    output = f"{secs} sec"
                else:
                    output = f"{secs} sec"

            # Mins
            elif mins == 1:
                output = f"{mins} min"
            else:
                output = f"{mins} mins"

        # Hours
        elif hours == 1:
            output = f"{hours} hr"
        else:
            output = f"{hours} hrs"

    # Days
    elif days == 1:
        output = f"{days} day"
    else:
        output = f"{days} days"

    return output


def commit(repo, message):
    """Add all and commit changes to current branch"""

    # Add all
    repo.index.add_all()
    repo.index.write()

    name = repo.config["User.name"]
    email = repo.config["User.email"]
    signature = git.Signature(name, email)
    tree = repo.index.write_tree()

    try:
        # Assuming prior commits exist
        ref = repo.head.name
        parents = [repo.head.target]
    except GitError:
        # Initial Commit
        ref = "HEAD"
        parents = []

    repo.create_commit(
        ref,
        signature,
        signature,
        message,
        tree,
        parents
    )


def getCommits(repo):
    """Returns a list commit objects"""

    commits = []
    last = repo[repo.head.target]
    for commit in repo.walk(last.id, GIT_SORT_TIME):
        timezoneInfo = timezone(timedelta(minutes=commit.author.offset))
        datetimeString = datetime.fromtimestamp(float(commit.author.time),
                                                timezoneInfo).strftime(GIT_TIME_FORMAT)

        commitDict = {}
        commitDict["id"] = commit.hex
        commitDict["name"] = commit.author.name
        commitDict["email"] = commit.author.email
        commitDict["date"] = datetimeString
        commitDict["message"] = commit.message.strip(" \t\n\r")

        commits.append(commitDict)

    return commits


def makeGitIgnore(path):
    """Generates .gitignore file for Git project at given path"""

    content = (
        "# Git\n"
        "*.blend1\n"
        "\n"
        "# Python\n"
        "# Byte-compiled / optimized / DLL files\n"
        "__pycache__/\n"
        "*.py[cod]\n"
        "*$py.class\n"
        "\n"
        "# C extensions\n"
        "*.so\n"
    )

    with open(os.path.join(path, ".gitignore"), "w") as file:
        file.write(content)


def configUser(repo, name, email):
    """Set user.name and user.email to the given Repo object"""

    repo.config["user.name"] = name
    repo.config["user.email"] = email
    repo.config["user.currentCommit"] = ""
    repo.config["user.backupSize"] = "0"


def getRepo(filepath):
    # Set up repository
    repo = git.Repository(filepath)

    return repo


def initialRepoSetup(filepath):
    # Make .gitignore file
    makeGitIgnore(filepath)

    # Init git repo
    repo = git.init_repository(filepath)

    # Get global/default git config if .gitconfig or .git/config exists
    try:
        defaultConfig = git.Config.get_global_config()
    except OSError:
        defaultConfig = {}

    username = (defaultConfig["user.name"]
                if "user.name" in defaultConfig else "Blender Version Control")

    email = (defaultConfig["user.email"]
             if "user.email" in defaultConfig else "blenderversioncontrol.415@gmail.com")

    # Configure git repo
    configUser(repo, username, email)

    # Initial commit
    commit(repo, "Initial commit - created project")


def deleteCommit(repo, delete_commit_id):
    previous_branch_ref = repo.branches[repo.head.shorthand]
    previous_branch_shorthand = previous_branch_ref.shorthand

    old_branch_name = f"delete_commit_{delete_commit_id}"

    previous_branch_ref.rename(old_branch_name)

    old_branch_iter = repo.walk(
        previous_branch_ref.target, GIT_SORT_REVERSE).__iter__()

    initial_commit = next(old_branch_iter)

    new_branch_ref = repo.branches.local.create(
        previous_branch_shorthand, initial_commit)
    repo.checkout(new_branch_ref)

    delete_commit_parents = None

    for commit in old_branch_iter:
        if commit.hex == delete_commit_id:
            delete_commit_parents = commit.parent_ids
            continue

        index = repo.index

        if str(commit.parent_ids[0]) == delete_commit_id:
            parents = delete_commit_parents

            repo.merge_commits(
                commit.id, delete_commit_id, favor="ours")
        else:
            parents = [repo.head.target]

            repo.cherrypick(commit.id)

        index.add_all()
        index.write()
        tree_id = index.write_tree()

        repo.create_commit(repo.head.name, commit.author, commit.committer,
                           commit.message, tree_id, parents)

        repo.state_cleanup()

    repo.branches[old_branch_name].delete()
