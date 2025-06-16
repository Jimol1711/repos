#!/bin/bash

# Fetch and prune
git fetch --prune

# Get real remote branches
remote_branches=$(git ls-remote --heads origin | awk '{print $2}' | sed 's|refs/heads/||')

# Get local branches
local_branches=$(git branch | sed 's/* //' | sed 's/ //g')

# Get current branch
current_branch=$(git branch --show-current)

# Delete local branches not in remote (except current)
for branch in $local_branches; do
  if ! echo "$remote_branches" | grep -Fxq "$branch"; then
    if [ "$branch" != "$current_branch" ]; then
      git branch -D "$branch"
    fi
  fi
done

# Create tracking branches for missing ones
for branch in $remote_branches; do
  if ! echo "$local_branches" | grep -Fxq "$branch"; then
    git branch --track "$branch" "origin/$branch" 2>/dev/null
  fi
done
