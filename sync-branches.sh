#!/bin/bash

# Fetch all remote branches and prune deleted ones
git fetch --all --prune

# Get list of remote branches (without origin/ prefix)
remote_branches=$(git branch -r | grep -v -e '->' -e 'HEAD' | sed 's|origin/||')

# Get list of local branches
local_branches=$(git branch | sed 's/* //' | sed 's/ //g')

# Delete local branches not in remote (except current branch)
for branch in $local_branches; do
  if ! echo "$remote_branches" | grep -Fxq "$branch"; then
    current_branch=$(git branch --show-current)
    if [ "$branch" != "$current_branch" ]; then
      git branch -D "$branch"
    fi
  fi
done

# Create missing local tracking branches
for branch in $remote_branches; do
  if ! echo "$local_branches" | grep -Fxq "$branch"; then
    git branch --track "$branch" "origin/$branch" 2>/dev/null
  fi
done
