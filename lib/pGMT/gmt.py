from .gmt_guru import GMTGuru



class GMT(GMTGuru):
    def __init__(self):
        self.stderr = None
        self.stdout = None


    def __getattr__(self, command):
        def f(*args, **kwargs):
            return self._gmtcommand(command, *args, **kwargs)
        return f

    def _gmtcommand(self, command, 
                          *args,
                          **kwargs):
        popen_args = _form_gmt_escape_shell_command(command, args, kwargs)
        p = subprocess.Popen(
            ' '.join(popen_args),
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            shell = True
            )
        self.stdout, self.stderr = p.communicate()
        
        if p.returncode != 0:
            print(self.stderr.decode())
            raise Exception(
                'Command %s returned an error. While executing command:\n%s'%\
                           (command, popen_args))


        
        
