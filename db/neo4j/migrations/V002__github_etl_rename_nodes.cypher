MATCH (c:Commit)
WITH COLLECT(c) AS node_list
CALL apoc.refactor.rename.label("Commit", "GitHubCommit", node_list)
YIELD committedOperations
RETURN committedOperations;
MATCH (c:PullRequest)
WITH COLLECT(c) AS node_list
CALL apoc.refactor.rename.label("PullRequest", "GitHubPullRequest", node_list)
YIELD committedOperations
RETURN committedOperations;
MATCH (c:Repository)
WITH COLLECT(c) AS node_list
CALL apoc.refactor.rename.label("Repository", "GitHubRepository", node_list)
YIELD committedOperations
RETURN committedOperations;
MATCH (c:Issue)
WITH COLLECT(c) AS node_list
CALL apoc.refactor.rename.label("Issue", "GitHubIssue", node_list)
YIELD committedOperations
RETURN committedOperations;
MATCH (c:Label)
WITH COLLECT(c) AS node_list
CALL apoc.refactor.rename.label("Label", "GitHubLabel", node_list)
YIELD committedOperations
RETURN committedOperations;
MATCH (c:Comment)
WITH COLLECT(c) AS node_list
CALL apoc.refactor.rename.label("Comment", "GitHubComment", node_list)
YIELD committedOperations
RETURN committedOperations;
MATCH (c:ReviewComment)
WITH COLLECT(c) AS node_list
CALL apoc.refactor.rename.label("ReviewComment", "GitHubReviewComment", node_list)
YIELD committedOperations
RETURN committedOperations;
MATCH (c:File)
WITH COLLECT(c) AS node_list
CALL apoc.refactor.rename.label("File", "GitHubFile", node_list)
YIELD committedOperations
RETURN committedOperations;