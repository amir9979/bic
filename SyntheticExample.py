import os
import shutil
import sys
import tempfile
from subprocess import run
import git
import pandas as pd

try:
    from javadiff.javadiff.diff import get_commit_diff
except:
    from javadiff.diff import get_commit_diff


def read_commit(repo_path):
    if type(repo_path) == type(''):
        repo = git.Repo(repo_path)
    df = pd.read_csv("TrainSet/train.csv")
    commits = df["commit"]
    commits_object = []
    for commit in commits[commits_start:commits_end]:
        commits_object.append(repo.commit(commit))
    return commits_object


def apply_diffmin(path_to_dir):
    # TODO jar
    # file_name = run(["java", "-jar", r"externals\target/diffmin-1.0-SNAPSHOT-jar-with-dependencies.jar",
    #                  os.path.join(path_to_dir, "before.java"), os.path.join(path_to_dir, "after.java")])
    # TODO: write to file in dir_repo
    with open(os.path.join(dir_repo, "test.java"), 'w', encoding="utf-8") as f:
        f.writelines("")
    commit_to_repo("test.java")


def commit_to_repo(file_name):
    # TODO: check with amir how we can don't write the before
    empty_repo.index.add([os.path.join(dir_repo, "before.java")])
    list_commits_repo.append(empty_repo.index.commit("before"))
    empty_repo.index.add([os.path.join(dir_repo, file_name)])
    list_commits_repo.append(empty_repo.index.commit("after"))


def write_file():
    for commit in all_commits:
        for parent in commit.parents:
            diff_index = parent.diff(commit)
            for diff in diff_index:
                try:
                    parent_contents = diff.a_blob.data_stream.read().decode('utf-8')
                    current_contents = diff.b_blob.data_stream.read().decode('utf-8')
                    with open(os.path.join(dir_repo, "before.java"), 'w', encoding="utf-8") as f:
                        f.writelines(parent_contents)
                    with open(os.path.join(dir_repo, "after.java"), 'w', encoding="utf-8") as f:
                        f.writelines(current_contents)
                    apply_diffmin(dir_repo)
                except:
                    pass

if __name__ == '__main__':
    window_size = 3
    ind = int(sys.argv[1])
    commits_start = ind * window_size
    commits_end = commits_start + window_size
    # repo_path = r"C:\Users\shirs\Downloads\commons-collections"
    repo_path = r"local_repo"
    all_commits = read_commit(repo_path)
    dir_repo = tempfile.mkdtemp()
    empty_repo = git.Repo.init(os.path.join(dir_repo, 'repo'))
    dir_repo = dir_repo + r"\repo"
    list_commits_repo = []
    write_file()

    metrics = []
    for commit in list_commits_repo:
        c = get_commit_diff(dir_repo, commit, analyze_diff=True)
        if c:
            metrics.extend(c.get_metrics())
    pd.DataFrame(metrics).to_csv(f'./results/{ind}.csv', index=False)

    if dir_repo:
        shutil.rmtree(dir_repo)
