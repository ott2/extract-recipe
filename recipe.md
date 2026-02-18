# Recipe for extract-recipe

## Session 1

### Prompt 1.1

For academic work we need to extract the recipes used to make artifacts with Claude Code. The most important part is probably the sequence of prompts related to a specific project, which is available via something like `grep path/to/project $HOME/.claude/history.jsonl | jq .display` except where something was pasted in, when we have to check the paste buffer referenced in the entry. Please make a Python project extract-recipe which makes a start on this, installable via pip and callable as the commandline script `extract-recipe`. Please ask me any questions you are unclear about before or during making the plan.

### Prompt 1.2

Just note: we probably need to do `python3 -m venv` to make a venv since global system pip will want to write to read-only locations. We also have other pythons available such as python3.14 if you prefer.

### Prompt 1.3

The python3 in the path is a poor choice since we should ideally make this work on a stock system, so /usr/bin/python3 would be better.

## Session 2

### Prompt 2.1

Please also document the exact installation required (like having to upgrade pip) in the README.md

### Prompt 2.2

Please set this up as a git repo and commit the project.

### Prompt 2.3

Please modify the code so the project can be specified by a unique substring. If there are two or more projects that match then the current "did you mean this" approach is fine.

### Prompt 2.4

Please modify this so it doesn't say "error" for multiple matches, but rather the previous-style "multiple projects match, please specify the path or an indentifying substring: <list of paths>" warning. Also we don't want "Error: ", if the user has asked for a project that doesn't match any of the ones we have then we should suggest running --list to see the list.

### Prompt 2.5

We should also be able to say "I want .../comparison not .../comparison2" without having to put in the full path. Maybe an option to use the supplied project string as the final component without substring matching?

### Prompt 2.6

When will `suggestions = _find_suggestions(args.project, all_paths)` fire?

### Prompt 2.7

The general idea is good, to do soft matching. Is there an easy way to do soft substring (rather than full string) matching without complex algorithms?

### Prompt 2.8

This sounds good, but I'm thinking that typos might also interchange a few characters; is there a library that handles this, or are we already needing a complex algorithm?

### Prompt 2.9

Do you think my approach of structuring Claude Code projects as separate subdirectories is a good match to what Claude Code is doing? If so, is just using the final path component going to be reasonably robust?

### Prompt 2.10

And we could then use `foo/a` and `foo/b` as unique project names, maybe even `o/a` and `o/b`? I like your suggestion to use soft matching for the final component. We should also document this pattern of disambiguating between different project names using the path separator, also in the commandline -h help.

### Prompt 2.11

Please also add 2-3 one-line examples to the -h help as a postfix.

### Prompt 2.12

I made a space tweak. Please commit.

### Prompt 2.13

Nice! Please now modify the date format to use ISO format YYYY-MM-DD. Also, is the microsecond timestamp relative to the system time or to some reference time somewhere on Earth?

### Prompt 2.14

Sorry, the time component was fine, I thought we were using %Y-%d-%m due to an older entry from early October that I read as 10 Jan.

### Prompt 2.15

Thanks! This is looking good. Please now add an option -a to extract all recipes. Do you think this is most naturally done by making a single output (for JSON this makes sense) or separate files (maybe for markdown)? If we are sticking to stdout then maybe -a would just create headings for each project?

### Prompt 2.16

If we pipe the output of this to `head` there is a scary-looking Python error. Can we handle broken pipe errors gracefully?

### Prompt 2.17

This is now working well, especially when used with `glow -p` as a markdown-capable pager. Please mention this in the README.md file.

### Prompt 2.18

Great! Please commit.

### Prompt 2.19

I would now like to push this to a new github repo. What `gh` commands would I run (starting with `gh auth` presumably)?

### Prompt 2.20

Is there a way to easily identify information in the recipe that might be private (like passwords, specifics of a user's local filesystem, or similar) so that it could be redacted with an option, like when sharing the recipe on github? Github does scans of public repo contents that contain things that look like auth tokens or passwords but it triggers an account lock so it would be good to avoid that happening rather than fixing after the fact.

### Prompt 2.21

What if there are multiple symlinks to the home directory?

### Prompt 2.22

That sounds fine.

## Session 3

### Prompt 3.1

Please now check that -r works as expected on _this_ project. After all we are going to push this to github.

### Prompt 3.2

The session IDs are potentially sensitive. With -r please replace those with "Session 1", "Session 2" and so on.

### Prompt 3.3

We do want the prompts to be anonymised as well, is this working correctly?

### Prompt 3.4

Are there any ID-looking strings across all project prompts?

### Prompt 3.5

There are still fairly specific project paths in some of these, which might be sensitive (like leaking details of current projects someone is working on). Any suggestions for redacting these?

### Prompt 3.6

Strip them please, they should not be part of the recipe. Do these actually appear when we do `grep projectpath ~/.claude/history.jsonl | jq .display` or is this something else?

### Prompt 3.7

Hmm. Could you give me a specific line from the history that shows this?

### Prompt 3.8

Which line number is that?

### Prompt 3.9

Hmm. So these lines from the history are not actually user prompts?

### Prompt 3.10

Is there any documentation about the format or intent of the ~/.claude/history.jsonl file at Anthropic or on the web?

### Prompt 3.11

We should have an option that keeps all of this, for instance if the user often edits plans (I don't think there is a record of what user changes were made to a plan?) but the default should be to strip these. Is there a reliable way to identify these as part of Claude Code internals rather than a particularly baroque user prompt?

### Prompt 3.12

What I am thinking about here is someone like gwern who often uses one model to create prompts, then uses that prompt in another model. I'm not sure these would all have the same "plan mode" marker we see in my own history. In addition, this prompt might change in future versions (by the way, we should document that this was developed with 2.1.45). Any ideas how to make this robust? I do agree we should not couple it to --redact as that replaces sensitive things inside prompts, this is more like removing system generated prompts from the recipe.

### Prompt 3.13

We might want to extend this to other frameworks like Antigravity or Codex, which likely have different patterns. Making --raw disable stripping, but --redact to remove sensitive paths from within the remaining entries (including system generated plans) seems like a reasonable use case. A list of common patterns like you were thinking makes sense, we could seed this from what we see from Claude Code and then later extend that if someone makes a PR adding Codex or Antigravity specific markers.

### Prompt 3.14

Is there a simple configuration file with the patterns stripped?

### Prompt 3.15

Let's make a file that is easy to edit.

### Prompt 3.16

Aren't we already using .toml in the project file?

### Prompt 3.17

What is your recommendation: is it worth using TOML here?

### Prompt 3.18

Some of the entries in the history are just `/clear` and other `/` commands without further modification. These should perhaps be stripped, what do you think? The `/compact <some comment>` lines seem worth keeping because those user-directions might be important if someone tries to replicate the recipe.

### Prompt 3.19

Actually, `/clear` probably should be treated like a kind of new session, but maybe marked slightly differently (it's the same session but with a clear break in context). `/compact` is similar to `/clear`.

### Prompt 3.20

The changes sound good. But can't we just add the other `/` commands to the existing patterns for stripping?

### Prompt 3.21

The filtering based on patterns should definitely happen on input, not output. `^/config\s*$` would match the `display` field contents for instance and could be stripped.

### Prompt 3.22

Does this handle the context break marking we discussed?

### Prompt 3.23

Please go ahead.

### Prompt 3.24

Looking at -a I see a lot of plans (97, 104, 105 etc.) which might be from older Claude Code using a different plan format. Please review.

### Prompt 3.25

The plans can be user-edited as well, but we have no record of edits they might have made. So indicating "here a planning step happened" seems useful by default but the whole plan should only be kept in raw mode. I'm also thinking that the numbering of prompts is not useful: the timestamp should be enough to identify it (although in raw mode maybe we want to also keep the original microsecond timestamp so it can be searched for easily in the raw logs).

### Prompt 3.26

Not sure about the horizontal line formatting after each prompt. What are the options in markdown for formatting the prompts? I'm not sure quote blocks are good because that usually adds spaces in front of each line which makes it less useful for copy-paste, and triple-backquote for code blocks might be a bit much.

### Prompt 3.27

Yes please.

### Prompt 3.28

In `extract-recipe -a` I see after `### [TIMESTAMP]` a single U and then our `Plan:` summary. Could you please investigate what is happening there?

### Prompt 3.29

I think the confusing thing here is that it wasn't clear it was not part of the plan summary on the next line. Maybe we should keep plan summaries looking more like prompts?

### Prompt 3.30

/commit

### Prompt 3.31

Please commit.

### Prompt 3.32

Please commit.

### Prompt 3.33

Please commit.

### Prompt 3.34

How are we doing detection of plan prompts?

### Prompt 3.35

Can't we just modify the regexp in the configuration file?

### Prompt 3.36

No, I don't mean adding sections. I was thinking just use /^plan-prefix.*plan-suffix$/ in some form.

### Prompt 3.37

(this requires not specialcasing \n as line delimiter)

### Prompt 3.38

`extract-recipe -ar` seems to collapse plans while `extract-recipe -a --raw` doesn't. Is this is a commandline processing bug?

### Prompt 3.39

We should pick -r for the one most likely to be used and -R for the slightly more unusual one. Which way round?

### Prompt 3.40

Plan files seem to match both the `.*\.jsonl$` style regexp and the "plan" prefix. It's not clear to me whether the configuration file is sensitive to ordering if a history entry matches more than one pattern.

### Prompt 3.41

Please commit.

### Prompt 3.42

For redaction, I'm seeing some paths like `/tmp` which potentially contain sensitive information. Are the redaction patterns configurable?

### Prompt 3.43

We should not hardcode configuration in the Python source. However, if we use pip install the configuration file currently will end up in some fairly obscure library path. Having it accessible more easily seems worthwhile. What do you think?

### Prompt 3.44

Do you think Claude Code will get confused or complain if we put files in its configuration directory?

### Prompt 3.45

That sounds good, I already have a bunch of directories in ~/.config but being able to override is sensible.

### Prompt 3.46

When we do pip install, will the configuration file be put in the right place?

### Prompt 3.47

Hmm. So how does the ordering in the file interact with the user patterns?

### Prompt 3.48

Hmm. I'm not sure we want there to be fixed default the user can't easily override without delving into (possibly read-only) Python library directories.

### Prompt 3.49

How about we have an option that copies the default config into ~/.config/ which the user can then edit?

### Prompt 3.50

Please commit.

### Prompt 3.51

Looking at the output of --redact, we should remove the timestamps as well, and use session_number.prompt_number numbering instead for this mode.

### Prompt 3.52

No, I was suggesting: Session 1 then Prompt 1.1, Prompt 1.2, Session 2

### Prompt 3.53

Please commit.

### Prompt 3.54

Please review the output of `extract-recipe -ar` for any additional things we should maybe redact.

### Prompt 3.55

That frequently used words pattern looks useful though on the input rather than the output (where it is dominated by the Prompt's we generated), maybe this would be a useful option? Some of the patterns you identified also sound useful to add to the config, just commented out by default.

### Prompt 3.56

I think if we are uncommenting OpenAI keys then we should uncomment Google and Anthropic ones too...

### Prompt 3.57

The stopwords should be a configuration file, and we should be able to turn it off (it might be useful to know one tends to use uppercased words), and we should maybe not just focus on the first word.

### Prompt 3.58

Makefile, Key, Files, Approach all sound reasonably common.

### Prompt 3.59

Should these not be regexps, maybe with implicit word-delimiters around them in how the regexp is interpreted?

### Prompt 3.60

If we are only matching words with starting caps then we could allow lowercase patterns that we modify? We should also note what redaction we do, and explicitly flag that it is not exhaustive; similarly the audit feature is just meant to find potential names that should be redacted manually or with other tools.

### Prompt 3.61

Please commit.

### Prompt 3.62

Do we have any obvious security problems, in particular with the configuration file? The threat model is that a malicious script modifies the file and when the user next runs extract-recipe bad things happen.

### Prompt 3.63

Please create a file SECURITY.md which discusses your analysis. This is excellent insight that we should preserve.

### Prompt 3.64

I also liked your suggestion that when --redact is used we should warn if no redaction happens (for instance, the user configuration file might be present but empty).

## Session 4 (context cleared)

## Session 5

### Prompt 5.1

In the Project Matching section of the README it's a little unclear what point 2 and 3 are or how they interact. Please look at this section and clarify. I have made other small edits to the file to redact local information which we want to keep.

### Prompt 5.2

I'm not sure we have an example of the usecase I am most likely to use, where we make a recipe.md file for a project developed with Claude Code.

### Prompt 5.3

If we use `.` for the project, what will happen? It might make sense to do the low-friction thing here.

### Prompt 5.4

Please commit.

### Prompt 5.5

What `gh` commands would I use to make a new github repo with this project, including adding a project description?

### Prompt 5.6

In recipe.md (made with extract-recipe -r . and lightly edited) I see a context cleared message. But there are several sessions; did we forget to deal with `/clear` in the same way we deal with new sessions or is this consistent with `/compact`?

### Prompt 5.7

OK, thanks for clarifying. I'm specifically thinking of --redact mode. Here the different session IDs are gone and we just have numbered sessions. It would seem to make sense in this context to indicate these as new sessions, with the Session header getting the indication of clear/compact (with or without message). What do you think?

### Prompt 5.8

Please commit.

### Prompt 5.9

I would like to include timestamps like `[TIMESTAMP]` in --redact, please modify the configuration file to handle this.

### Prompt 5.10

Please add an option to specify the main header for the markdown file explicitly (the current `extract-recipe -r .` leaks information about . which might be sensitive), and document it.

### Prompt 5.11

Please also make a makefile for `make recipe` that uses the title `Recipe for extract-recipe`.

### Prompt 5.12

OK, this has Recipe: Recipe, maybe just use the title as-is.

### Prompt 5.13

Maybe specify when redaction was used, `Recipe (redacted): ` in this case?

### Prompt 5.14

Please add the makefile and `recipe.md` then commit.

### Prompt 5.15

We need to mention that `make recipe` can be used to make the recipe for this repo and that the recipe is in `recipe.md` (linked so it becomes available to be clicked on github).

## Session 6

### Prompt 6.1

Please now do that, and commit.
