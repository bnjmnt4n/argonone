{ lib
, buildPythonPackage
, fetchFromGitHub
, colorzero
, withPigpio ? true, pigpio-py ? null
, withRpiGpio ? false, rpi-gpio ? null
, withRpio ? false, rpio ? null
, pytestCheckHook
, mock
}:

buildPythonPackage rec {
  pname = "gpiozero";
  version = "1.5.1";

  src = fetchFromGitHub {
    owner = "gpiozero";
    repo = pname;
    rev = "v${version}";
    sha256 = "17fr7bilrhrb6r7djb41g317lm864kd4bkrl22aqhk4236sqq9ym";
  };

  postPatch = ''
    substituteInPlace gpiozero/pins/local.py --replace "raise PinUnknownPi('unable to locate Pi revision in /proc/device-tree or /proc/cpuinfo')" "return int('d03114', base=16)"
  '';

  propagatedBuildInputs = [ colorzero ]
    ++ lib.optionals (withPigpio) [ pigpio-py ]
    ++ lib.optionals (withRpiGpio) [ rpi-gpio ]
    ++ lib.optionals (withRpio) [ rpio ] ;

  checkInputs = [ pytestCheckHook mock ];
  pythonImportsCheck = [ "gpiozero" ];
  dontUseSetuptoolsCheck = true;
  preCheck = "pushd $TMP/$sourceRoot";
  postCheck = "popd";
  doCheck = false;

  meta = with lib; {
    description = "A simple interface to GPIO devices with Raspberry Pi";
    homepage = "https://gpiozero.readthedocs.io/en/stable/";
    license = licenses.bsd3;
    maintainers = [ maintainers.drewrisinger ];
    isRpiPkg = true;
  };
}
