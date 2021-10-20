import os
import shutil
import sys
import tempfile
import subprocess
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
    # TODO: uncomment
    file = subprocess.check_output(["C:\hostedtoolcache\windows\Java_Adopt_jdk", "-v", "11.0.12-7", "--exec",
                                    "java", "-jar", r"externals/diffmin-1.0-SNAPSHOT-jar-with-dependencies.jar",
                     os.path.join(path_to_dir, "before.java"), os.path.join(path_to_dir, "after.java")])
    # file = subprocess.check_output(["java", "-jar", r"externals/diffmin-1.0-SNAPSHOT-jar-with-dependencies.jar",
    #                                 os.path.join(path_to_dir, "before.java"), os.path.join(path_to_dir, "after.java")])
    print("s")
    with open(os.path.join(dir_repo, "new.java"), 'w', encoding="utf-8") as f:
        f.writelines(str(file))
    commit_to_repo("new.java")


def commit_to_repo(file_name):
    # TODO check if this ok don't write before
    empty_repo.index.add([os.path.join(dir_repo, "before.java")])
    list_commits_repo.append(empty_repo.index.commit("before"))
    empty_repo.index.add([os.path.join(dir_repo, file_name)])
    list_commits_repo.append(empty_repo.index.commit("after"))
    print("d")


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
                except Exception as e:
                    print(e)
                    pass


if __name__ == '__main__':
    window_size = 1
    ind = int(sys.argv[1])
    commits_start = ind * window_size
    commits_end = commits_start + window_size
    # repo_path = r"C:\Users\shirs\Downloads\commons-collections"
    # TODO: uncomment
    repo_path = r"local_repo"
    all_commits = read_commit(repo_path)
    dir_repo = tempfile.mkdtemp()
    empty_repo = git.Repo.init(os.path.join(dir_repo, 'SyntheticExample'))
    dir_repo = dir_repo + r"\SyntheticExample"
    list_commits_repo = []
    write_file()

    metrics = []
    for commit in list_commits_repo:
        # TODO: True
        c = get_commit_diff(dir_repo, commit, analyze_diff=False)
        if c:
            metrics.extend(c.get_metrics())
    # print(metrics)
    pd.DataFrame(metrics).to_csv(f'./results/{ind}.csv', index=False)
    # empty_repo.create_remote('origin', 'https://github.com/shirshir05/SyntheticExample.git')
    # empty_repo.remote("origin").push("master")
    if dir_repo:
        shutil.rmtree(dir_repo)