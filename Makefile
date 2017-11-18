.PHONY: doc

#####

# ATTENTION!
#
# all this stuff should only be run on a raspberry pi otherwise the results are undefined
#
#####

doc:
	mkdir -p docs/html
	pydoc3 -w `find autopylot -name '*.py'`
	mv *.html docs/html

test:
	./setup.py test

install:
	./setup.py install
