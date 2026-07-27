from github import Github


def get_latest_commit():

    github = Github()

    repo = github.get_repo("feranzeey/platformops-ai")

    commits = repo.get_commits()

    latest = commits[0]

    return {
        "author": latest.author.login,
        "message": latest.commit.message,
        "date": str(latest.commit.author.date)
    }