#!/usr/bin/env python
"""
Author Naveen Joy najoy@cisco.com
Parses an input yang module and generates SQLAlchemy Model objects

Usage: Set the YANGMODULE variable below and run the program to generate the parsed output
"""
import os, imp, subprocess
import shlex, time
import pyangbind

YANGMODULE="gluon-port.yang"
#YANGMODULE="test/openconfig-local-routing.yang"

class CommandExecutionError(Exception):
    """Base Exception class for all command execution errors."""
    def __init__(self, *args):
        Exception.__init__(self, *args)

class BindingsError(Exception):
    """Base Exception class for all binding errors."""
    def __init__(self, *args):
        Exception.__init__(self, *args)

class PyMod:
    """
    Creates and manages the python object tree of the YANG module
    """
    def __init__(self):
        self.this_dir = None
        self.yang_module = None
        self.bindings_file = self.generate_python_bindings()
        self.set_bindings()
        self.yang_mod = self.get_module_instance()
       
    def set_bindings(self):
        """
        set the self.bindings attribute after waiting for the bindings file to be generated
        """
        time_out = 10
        while time_out > 0:
            time.sleep(1)
            try:
                self.bindings = imp.load_source('binding', self.bindings_file)
            except Exception:
                pass
            if self.get_module_name() is None:
                time_out -= 1
            else:
                return
        raise BindingsError("Cound not generate valid bindings for yang module: %s" % self.yang_module)

    def generate_python_bindings(self, yang_file=YANGMODULE):
        """
        Generates Yang to python bindings file for the input yang module
        param: yang_file: File name of the yang module
        rtype: string
        """
        self.this_dir = os.path.dirname(os.path.realpath(__file__))
        pyang_plugin = "%s/plugin" % os.path.dirname(pyangbind.__file__)
        binding_name = "binding.py"
        ## TODO remove any existing bindings file
        binding_path = "%s/%s" % (self.this_dir, binding_name)
        self.yang_module = "%s/%s" % (self.this_dir, yang_file)
        cmd = "pyang"
        cmd += " --plugindir %s" % pyang_plugin
        cmd += " -f pybind -o %s" % binding_path
        cmd += " -p %s" % self.this_dir
        cmd += " %s" % self.yang_module 
        cmd = shlex.split(cmd)
        #print("cmd = %s" % cmd)
        self._run_command(cmd)
        return binding_path

    def get_module_name(self):
        """
        Return the python class name of the yang module
        """
        cmd = "pyang -f tree -p %s %s" % (self.this_dir, self.yang_module)
        yang_tree = self._run_command(shlex.split(cmd))
        mod_yang_name = yang_tree.split()[1]
        #print("module yang name: %s" % mod_yang_name)
        #print("attrs: %s" % dir(self.bindings))
        for attr in dir(self.bindings):
            if not attr.startswith("_"):
                obj = getattr(self.bindings, attr)
                #print("checking object: %s" % attr)
                if hasattr(obj, '_yang_name'):
                    obj_yang_name = getattr(obj, '_yang_name')
                    #print("object %s yang name: %s" % (attr, obj_yang_name))
                    if obj_yang_name == mod_yang_name:
                        return attr

    def get_module_instance(self):
        """
        Return and instance of the yang module object
        """
        module_name = self.get_module_name()
        #print("module_name = %s" % module_name)
        return getattr(self.bindings, module_name)()

    def _run_command(self, cmd, cmd_input=None):
        """
        Run a system command and return the output as a utf-8 encoded string
        param: cmd: a list of command and its arguments
        param: cmd_input: input data to the command
        """
        pipe = subprocess.PIPE
        proc = subprocess.Popen(cmd, shell=False, stdin=pipe, stdout=pipe,
                                stderr=pipe, close_fds=True)
        (out, err) = proc.communicate(cmd_input)
        if proc.returncode != 0:
            raise CommandExecutionError(err)
        return out.decode('utf-8')

    
    def parse(self):
        """
        output a python dict after parsing the Yang module
        <container>:{ "yang_type" : <yang_data_type>,
                      <attribute.1>:{ "yang_type": <yang_data_type>,
                                      "data_type": <if_leaf_node_its_data_type> else <if_container_its_attribute_dict>
                                    }
                      <attribute.n> :{ "yang_type": <yang_data_type>,
                                      "data_type": <if_leaf_node_its_data_type> else <if_container_its_attribute_dict>
                                     } 
                     }
        Note: Limited to parsing nodes of type containers and leafs
        TODO// Add lists, enumeration and other types
        """
        #Create a python dictionary representation of the input yang element
        def compose_elements(e=None, eName=None):
            if e is None:
                e = self.yang_mod
            if eName is None:
                eName = "root"
            p = {}
            #print("Dir(%s) = %s" % (eName, dir(e)))
            #iterate through the pyangbind elements
            for element_name in getattr(e, "_pyangbind_elements"):
                #Get the element
                element = getattr(e, element_name)
                if hasattr(element, "yang_name"):
                    #retrieve the YANG name method
                    yang_name = getattr(element, "yang_name")
                    element_id = yang_name()
                else:
                    element_id = element_name
                #print("processing element: %s" % element_id)
                #print("Dir(%s) = %s" % (element_id, dir(element)))
                if hasattr(element, "_is_container") and getattr(element, "_is_container") is not False:
                    yang_type = getattr(element, "_is_container")
                    if yang_type == "container":
                        #print("Element %s has yang_type: %s" % (element_id, yang_type))
                        p[element_id] = compose_elements(e=element, eName=element_id)
                        p[element_id]["yang_name"] = element_id
                        p[element_id]["yang_type"] = yang_type
                elif hasattr(element, "_is_leaf") and getattr(element, "_is_leaf"):
                    #print("Element %s has yang_type: %s" % (element_id, "leaf"))
                    l = {}
                    l["yang_name"] = element_id
                    l["yang_type"] = "leaf"
                    if hasattr(element, "_base_type"):
                        l["data_type"] = getattr(element, "_base_type")
                    p[element_id] = l
            return p 
        return compose_elements()


    def describe(self):
        """
        Return a python dict like representation of the yang module
        """
        #return self.get_module_instance().get()
        return self.parse()


if __name__ == "__main__":
    print(PyMod().describe())

