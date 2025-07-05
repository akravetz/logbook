You have three modes of operation:

1. Plan mode - You will work with the user to define a plan, you will gather all the information you need to make the changes but will not make any changes
2. Act mode - You will make changes to the codebase based on the plan
3. Review mode - review changes you made to the codebase based on changes in the current git branch

## PLAN MODE
Follow these steps:
- Print `# Mode: PLAN`
- Work with the user to develop a plan for the feature they are interested in implementing.  This plan should include a discrete list of tasks to complete in order with enough detail in each task such that someone reading the plan with only the codebase as context could understand what needs to be implemented
- Once the user is satisfied with the plan, they will type "ACT"
- Once the user types "ACT" create a new github issue using `gh issue create --title "<title of bug/feature to implement> --label <bug/feature> --body <plan text with [ ] boxes that you will check off as you complete each task>"`
- Begin implementing the tasks in the plan one by one.  As you complete each task update the github issue text using `gh issue edit <issue id> --body "updated text"` where updated text includes the text of the plan with `[ ]` changed to `[x]` for the task that has been complete

User's requested feature or bug fix: $ARGUMENTS
