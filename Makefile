.PHONY: doc

doc:
	mkdir -p docs/html
	pydoc3 -w `find autopylot -name '*.py'`
	mv *.html docs/html

test:
	./setup.py test

install:
	./setup.py install
