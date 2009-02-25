

all: bertrand/bert

bertrand/:
	git clone git@github.com:npryce/bertrand.git bertrand/

bertrand/bert: bertrand/
	(cd bertrand ; $(MAKE) $(MAKEFLAGS))


clean:
	rm -rf bertrand/

