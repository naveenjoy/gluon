#!/usr/bin/env python
"""
Author Naveen Joy najoy@cisco.com
Parses an input yang module and generates SQLAlchemy Model objects
"""
import os, imp
import pyangbind

#YANGMODULE="gluon-port.yang"
YANGMODULE="test/openconfig-local-routing.yang"

class PyMod:
    """
    Creates and manages the python object of the YANG module
    """
    def __init__(self):
        self.bindings_file = None
        self.generate_python_bindings()
        self.bindings = imp.load_source('binding', self.bindings_file)

    def generate_python_bindings(self, yang_file=YANGMODULE):
        """
        Generates Yang to python bindings file for the input yang module
        param: yang_file: File name of the yang module
        rtype: string
        """
        if self.bindings_file is None:
            this_dir = os.path.dirname(os.path.realpath(__file__))
            pyang_plugin = "%s/plugin" % os.path.dirname(pyangbind.__file__)
            binding_name = "binding.py"
            binding_path = "%s/%s" % (this_dir, binding_name)
            cmd = "%s " % "pyang"
            cmd += "--plugindir %s" % pyang_plugin
            cmd += " -f pybind -o %s" % binding_path
            cmd += " -p %s" % this_dir
            cmd += " %s/%s" % (this_dir, yang_file)
            #print(cmd)
            os.system(cmd)
            self.bindings_file = binding_path

    def get_module_name(self):
        """
        Return the python class name of the yang module
        //TODO: Reliable way to determine module name
        module = pyang -f tree test/openconfig-local-routing.yang | grep module: | awk '{print $2}'
        """
        for attr in dir(self.bindings):
            if not attr.startswith("_"):
                if hasattr(getattr(self.bindings, attr), '_yang_name'):
                    return attr

    def get_module_instance(self):
        """
        Return and instance of the yang module object
        """
        module_name = self.get_module_name()
        print(module_name)
        return getattr(self.bindings, module_name)()

    def describe(self):
        """
        Return a python dict like representation of the yang module
        """
        return self.get_module_instance().get()


if __name__ == "__main__":
    print(PyMod().describe())

