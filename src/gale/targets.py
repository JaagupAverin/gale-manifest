from dataclasses import dataclass


@dataclass
class Target:
    name: str


HMI_APP_TARGET = Target("hmi_app")

TARGETS: list[Target] = [HMI_APP_TARGET]


def get_target_names() -> list[str]:
    return [target.name for target in TARGETS]
