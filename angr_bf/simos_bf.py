from angr.simos import SimOS, register_simos
from angr.procedures import SIM_PROCEDURES as P, SIM_LIBRARIES as L
from angr.procedures.definitions import SimSyscallLibrary
from angr import SimProcedure
from angr.calling_conventions import SimCC, register_syscall_cc, register_default_cc, SimCCUnknown
from angr_bf.arch_bf import ArchBF


class WriteByteAtPtr(SimProcedure):
    """
    Defines what to do for the "." instruction.
    """

    IS_SYSCALL = True
    NUM_ARGS = 0
    num_args = 0
    # pylint:disable=arguments-differ

    def run(self, state):
        # pylint:disable=unused-argument
        fd = 1  # POSIX STDOUT
        data = self.state.memory.load(self.state.regs.ptr, 1)
        self.state.posix.write(fd, data, 1)
        return None


class ReadByteToPtr(SimProcedure):
    """
    Defines what to do for the "," instruction
    """

    IS_SYSCALL = True
    num_args = 0
    NUM_ARGS = 0
    # pylint:disable=arguments-differ

    def run(self, state):
        fd = 0 # Posix STDIN
        self.state.posix.read(fd, self.state.regs.ptr, 1)
        # NOTE: The behavior of EOF (this is zero) is undefined!!!
        return None


P['bf'] = {}
P['bf']['write_byte_at_ptr'] = WriteByteAtPtr
P['bf']['read_byte_to_ptr'] = ReadByteToPtr

syscall_lib = SimSyscallLibrary()
syscall_lib.set_library_names('brainfuck')
syscall_lib.add_all_from_dict(P['bf'])
syscall_lib.add_number_mapping_from_dict('BF', {0 : 'read_byte_to_ptr',
                                                1 : 'write_byte_at_ptr'})

class SimBF(SimOS):
    """
    Defines the "OS" of a BrainFuck program.

    This means:
    -  The memory layout (separate code and data)
    -  The "syscalls" (read stdin and write stdout)

    """

    def __init__(self, *args, **kwargs):
        super(SimBF, self).__init__(*args, name="BF", **kwargs)

        self.syscall_library = L['brainfuck']

    def configure_project(self):
        super(SimBF, self).configure_project()

    def state_blank(self, data_region_size=0x8000, **kwargs):
        # pylint:disable=arguments-differ
        state = super(SimBF, self).state_blank(**kwargs)  # pylint:disable=invalid-name
        # PTR starts halfway through memory
        state.regs.ptr = 0x80000000
        state.memory.map_region(state.regs.ptr, data_region_size, 3, init_zero=True)
        return state

    def state_entry(self, **kwargs):
        state = super(SimBF, self).state_entry(**kwargs)
        return state


class SimBFSyscall(SimCC):
    """
    This defines our syscall format.
    Obviously this is pretty dumb, for BrainFuck
    This is really just here to make the two simprocedures work.
    """

    # No need to pull the regs out, we always just want ptr straight up.
    # THis is usually a list of string register names.
    ARG_REGS = [ 'ptr' ]
    # We never return anything to registers, but if we did, we'd use a RegArg object here.
    #RETURN_VAL = ""
    ARCH = ArchBF

    @staticmethod
    def _match(arch, args, sp_delta):   # pylint: disable=unused-argument
        # doesn't appear anywhere but syscalls
        return False

    @staticmethod
    def syscall_num(state):
        return state.regs.inout


register_simos('bf', SimBF)
register_syscall_cc('BF','default',SimBFSyscall)
register_default_cc('BF',SimCCUnknown)
