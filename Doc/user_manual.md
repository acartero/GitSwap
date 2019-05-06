[Home](../readme.md)

User manual
-----------
This tool allows you to work on the current branch until the most recent commit with two parents commits 
(usually a merge commit).

In the main menu:  
- Use "Select path" button to choose a git repository.
- Use the "Merge" button after selecting several commits with "shift+click".
- Double click on a commit to reword it.
- Click on a single commit and use the "Split" button to split it into two commits.
- Click on "Commit everything" to apply the modifications to your history. 
All modifications are stashed and a tag is placed before this operation, to let you go back if you are not satisfied with the result.

Advanced interactions in the main menu:
- Drag and drop a commit to reorder your history
- When you click on a commit, conflicting commits are automatically detected: these are the yellow commits. 
- You can freely reorder commits which do not conflict, but a merge window is automatically opened each time you swap conflicting commits. 
 
In the merge menu:
- Select one or several lines, and press "s" to **s**wap them.
- Use "Swap" to move all the lines from the right commit to the left, and all the lines from the left commit to the right. This is applied **for all files**.
- Use "Reset" to reset all additions/deletions to their original commit **for all files**.
- Use "Move left" and "Move right" to move all additions/deletions left or right **for the current file**.
- Use "Apply" to validate your modifications, or close the window to cancel the operation.
