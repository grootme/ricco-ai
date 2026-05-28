from setuptools import setup, find_packages
setup(
    name="ricco_verticals",
    version="1.0.0",
    description="Industry-Specific Solutions",
    author="RICCO Team",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    entry_points={"frappe_app": ["ricco_verticals = ricco_verticals"]}
)
