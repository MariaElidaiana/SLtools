TARGET = compute_nfw_lens_parameters
INTERFACE = compute_nfw_lens_parameters.i
WRAPFILE = $(TARGET)_wrap.c
WRAPOBJ = $(TARGET)_wrap.o
MODULE = _$(TARGET).so
SRCS = compute_nfw_lens_parameters.cpp
COBJS = $(SRCS:.cpp=.o)
SWIGOPT = -python
PYTHONBIN = $(shell echo `which python`)
PYTHONINC = $(shell echo "import sys; print sys.prefix+'/include/python'+str(sys.version_info[0])+'.'+str(sys.version_info[1])" | ${PYTHONBIN})

all: compute_nfw_lens_parameters

compute_nfw_lens_parameters: compute_nfw_lens_parameters.cpp
	g++ -Wall -lm $(SRCS) -o $(TARGET)

module_lnx: $(SRCS) $(INTERFACE)
	swig $(SWIGOPT) $(INTERFACE)
	g++ -Wall -lm -fpic -c $(SRCS) $(WRAPFILE) -I$(PYTHONINC)
	g++ -shared $(COBJS) $(WRAPOBJ) -o $(MODULE)

module_mac: $(SRCS) $(INTERFACE)
	swig $(SWIGOPT) $(INTERFACE)
	g++ -I$(PYTHONINC) -framework Python -bundle -bundle_loader $(PYTHONBIN) $(SRCS) $(WRAPFILE) -o $(MODULE)

clean: 
	@rm -f $(TARGET) $(WRAPFILE) $(WRAPOBJ) $(COBJS)

