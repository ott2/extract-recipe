recipe:
	extract-recipe -r -t "Recipe for extract-recipe" . -o recipe.md

test-3.14:
	python3.14 -m venv .venv-3.14
	.venv-3.14/bin/pip install --upgrade pip
	.venv-3.14/bin/pip install .
	.venv-3.14/bin/extract-recipe --help
	.venv-3.14/bin/extract-recipe --list

clean:
	rm -rf .venv-3.14
