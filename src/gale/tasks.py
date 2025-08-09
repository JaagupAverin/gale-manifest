import shutil
import socket
import time
from pathlib import Path

from gale import log
from gale.configuration import Configuration
from gale.data.boards import NRF5340_BSIM_BOARD
from gale.data.projects import SHARED_PROJECT, ZEPHYR_PROJECT
from gale.data.structs import Board, BuildCache, BuildType, Target
from gale.util import CmdMode, run_command


def task_run_app_in_bsim(  # noqa: PLR0915
    cache: BuildCache,
    *,
    gdb: bool,
    real_time: bool,
    tracing: bool = True,
) -> None:
    """Given that the target was built as a BabbleSim executable, runs the binary natively.

    This entails:
    1. Copying the required bsim binaries/libraries and the target binary to a common directory;
    2. Creating a common simulation ID;
    3. Running the target binary device;
    4. Running optional devices, such as the handbrake device (if "real time" execution is required);
    5. Running the phy layer;

    Args:
        cache: used to locate all build artifacts, and determine location of tools, such as gdb or BabbleSim.
        gdb: if True, runs the app with gdb (client with TUI);
        real_time: if True, the simulation will run in "real time", i.e K_SECONDS(1) corresponds to 1 second in reality;
            if False, the simulation runs at maximum speed (limited only by host CPU); good for running tests;
        tracing: if True, passes the --trace-file argument to the BabbleSim executable in order to store trace data
            (trace data is stored into the final run/results directory);
        trace_dir: if True, generated trace data into the specified directory;
            if False, trace data is still be generated, but into an unspecified directory;
    """
    exe: Path = Path(cache.cmake_cache.exe_path)
    if not exe.exists():
        log.fatal(f"Output binary '{exe}' does not exist; use build first.")

    # Inputs:
    bsim_build_dir: Path = Path(cache.cmake_cache.bsim_out_path)
    bsim_bin_dir: Path = bsim_build_dir / "bin"
    bsim_lib_dir: Path = bsim_build_dir / "lib"

    # Outputs:
    final_dir: Path = cache.target.parent_project.dir / "bsim" / cache.triplet
    final_bin_dir: Path = final_dir / "bin"
    final_lib_dir: Path = final_dir / "lib"
    final_results_dir: Path = final_dir / "results"

    final_dir.mkdir(parents=True, exist_ok=True)
    final_results_dir.mkdir(parents=True, exist_ok=True)

    common_args = ""

    # All devices shall be "linked together" by the same simulation ID;
    # Once the phy is executed, all devices with the same simulation ID will share the same phy:
    sim_id: str = cache.target.name
    num_devices: int = 0

    # 1. Prepare simulation environment by copying the bsim binaries and libraries to the final folder:
    log.dbg(f"Preparing to run executable inside {final_bin_dir}")
    shutil.copytree(bsim_bin_dir, final_bin_dir, dirs_exist_ok=True)
    shutil.copytree(bsim_lib_dir, final_lib_dir, dirs_exist_ok=True)

    # 2. Copy the app device itself to the final folder:
    log.dbg(f"Copying executable from {exe}")
    final_exe: str = str(shutil.copy(exe, final_bin_dir))

    # 3. Prepare tracing if required:
    if tracing:
        # Copy Zephyr's metadata file to same directory as our final trace data file:
        trace_metadata = f"{ZEPHYR_PROJECT.dir / 'subsys/tracing/ctf/tsdl/metadata'}"
        shutil.copy(trace_metadata, final_results_dir / "metadata")

        # Tell application to output trace data to custom file:
        trace_file_arg = f"--trace-file={final_results_dir}/trace_data"
        common_args += f" {trace_file_arg}"

    # Use a well-defined path for the flash binary, which is used for persistent storage of flash data:
    if cache.board == NRF5340_BSIM_BOARD:
        # This board needs to separate flash files for app and net domains:
        simulated_flash_bin_arg: str = (
            f"--flash_app_file={final_results_dir}/flash_app.bin"
            + f" --flash_net_file={final_results_dir}/flash_net.bin"
        )
    else:
        # Assume a single argument; although this may also vary depending on hw models;
        simulated_flash_bin_arg = f"--flash_file={final_results_dir}/flash.bin"

    common_args += f" {simulated_flash_bin_arg}"

    # How often the handbrake triggers or "pokes" the simulation:
    # Decreasing improves responsiveness, but increases overhead; should not be reduced below 2ms.
    bsim_handbrake_interval_nsec: int = 5_000
    if real_time:
        # MRO: Max Resync Offset; determines max offset from PHY time before the app must resync;
        # default value is 1sec, but lowering this makes the app more responsive,
        # which is especially important if using handbrake and responsiveness is needed.
        common_args += f" --mro={bsim_handbrake_interval_nsec}"

    # 4. Run application device itself:
    if gdb:
        gdbinit: Path = SHARED_PROJECT.dir / "share" / "gdb" / ".gdbconf"
        # In case of debugging, we cannot attach to UART in the same terminal as gdb, so instead we
        # print out a message instructing the user to attach the UART, and wait until it is attached.
        # TODO: Can launch with gdbserver instead in the future if want to attach from IDE.
        uart_attach_cmd: str = r"echo App\ halted\ until\ UART\ attached!\ Use:\ gale\ monitor\ --port\ %s"
        uart_args = (
            "--uart_pty_wait"
            + f' --uart0_pty_attach_cmd="{uart_attach_cmd}"'
            + f' --uart1_pty_attach_cmd="{uart_attach_cmd}"'
        )
        app_run_cmd: str = (
            f"{cache.cmake_cache.gdb} --tui -x {gdbinit} --args "
            f"{final_exe} -s={sim_id} -d={num_devices} {uart_args} {common_args}"
        )
        num_devices += 1
        run_command(
            cmd=app_run_cmd,
            desc=f"Running target '{cache.target.name}' device in BabbleSim",
            cwd=final_bin_dir,
            mode=CmdMode.SPAWN_NEW_TERMINAL,
        )
    else:
        # In case of running directly, attach the UART immediately:
        uart_attach_cmd = "gale monitor --port %s --new-terminal"
        uart_args = (
            "--uart_pty_wait"
            + f' --uart1_pty_attach_cmd="{uart_attach_cmd}"'
            + f' --uart4_pty_attach_cmd="{uart_attach_cmd}"'
        )

        app_run_cmd = f"{final_exe} -s={sim_id} -d={num_devices} {uart_args} {common_args}"
        num_devices += 1
        run_command(
            cmd=app_run_cmd,
            desc=f"Running target '{cache.target.name}' device in BabbleSim",
            cwd=final_bin_dir,
            mode=CmdMode.BACKGROUND,
        )

    # 5. Run the handbrake device, if real time is requested:
    if real_time:
        handbrake_run_cmd: str = (
            f"./bs_device_handbrake -s={sim_id} -d={num_devices} --pp={bsim_handbrake_interval_nsec}"
        )
        num_devices += 1
        run_command(
            cmd=handbrake_run_cmd,
            desc="Running handbrake device in BabbleSim",
            cwd=final_bin_dir,
            mode=CmdMode.BACKGROUND,
        )

    # 6. Run the PHY itself, which starts the simulation proper:
    phy_run_cmd: str = f"./bs_2G4_phy_v1 -s={sim_id} -D={num_devices}"
    run_command(
        cmd=phy_run_cmd,
        desc="Starting BabbleSim PHY",
        cwd=final_bin_dir,
        mode=CmdMode.FOREGROUND,
    )


def is_localhost_port_open(port: int, timeout: float = 10.0) -> bool:
    start: float = time.time()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        while time.time() - start < timeout:
            res: int = s.connect_ex(("localhost", port))
            if res == 0:
                return True
            time.sleep(0.1)
    return False


def run_codechecker(board: Board, target: Target) -> None:
    """Analyze the project with CodeChecker SCA.

    This involves:
        * building the target;
        * starting CodeChecker server;
        * storing the build results into the server;
        * connecting to the server with a web browser;
    """
    # 1. Build the target with SCA enabled
    conf: Configuration = Configuration(board, target, build_type=BuildType.SCA)
    cache: BuildCache = conf.build(pristine=True, load_extra_args_from_disk=True)

    # 2. Start the CodeChecker server
    run_command(
        cmd=f"{cache.cmake_cache.codechecker_exe} server",
        desc="Starting CodeChecker server",
        cwd=cache.build_dir,
        mode=CmdMode.SPAWN_NEW_TERMINAL,
    )
    if is_localhost_port_open(8001):
        log.inf("CodeChecker server started")
    else:
        log.fatal("CodeChecker server failed to start")

    # 3. Store the analysis results into the CodeChecker server
    sca_results_dir: Path = cache.build_dir / "sca" / "codechecker" / "codechecker.plist"
    run_command(
        cmd=f"{cache.cmake_cache.codechecker_exe} store {sca_results_dir} -n {target.name}",
        desc="Storing analysis results into CodeChecker server",
        cwd=cache.build_dir,
        mode=CmdMode.FOREGROUND,
    )

    # 4. Open localhost:8001 in native browser
    run_command(
        cmd="open http://localhost:8001",
        desc="Opening CodeChecker in browser",
        cwd=cache.build_dir,
        mode=CmdMode.FOREGROUND,
    )
