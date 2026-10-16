"""Small synthetic tests; these are not CFD results."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import numpy as np
from postprocess_forces import force_scale, read_coefficients, window_statistics


class PostprocessTests(unittest.TestCase):
    def test_nonuniform_time_integration_and_endpoints(self):
        t = np.array([0.0, 0.3, 1.1, 2.0])
        cd, cl = 1 + t, 2 * t - 1
        result = window_statistics(t, cd, cl, 0.2, 1.8)
        self.assertAlmostEqual(result['Cd_mean'], 2.0)
        self.assertAlmostEqual(result['Cl_half_peak_to_peak'], 1.6)
        np.testing.assert_allclose(result['Cd_range'], [1.2, 2.8])

    def test_ten_column_input(self):
        with TemporaryDirectory(prefix='.test_tmp', dir=Path(__file__).parent.parent) as tmp:
            path = Path(tmp) / 'force.dat'
            data = np.zeros((3, 10))
            data[:, 0] = [0, 1, 2]
            data[:, 1] = 2 * force_scale
            data[:, 2] = np.array([-1, 0, 1]) * force_scale
            data[:, 4:7] = 0.75 * data[:, 1:4]
            data[:, 7:10] = 0.25 * data[:, 1:4]
            np.savetxt(path, data)
            t, cd, cl = read_coefficients(path)
            np.testing.assert_allclose(cd, 2)
            np.testing.assert_allclose(cl, [-1, 0, 1])
            data[:, 0] = [0, 1, 1]
            np.savetxt(path, data)
            with self.assertRaises(ValueError):
                read_coefficients(path)
            data[:, 0] = [0, 1, 2]
            data[1, 4] = 9
            np.savetxt(path, data)
            with self.assertRaises(ValueError):
                read_coefficients(path)
            np.savetxt(path, data[:, :4])
            with self.assertRaises(ValueError):
                read_coefficients(path)

    def test_window_outside_records(self):
        with self.assertRaises(ValueError):
            window_statistics(np.array([0., 1.]), np.ones(2), np.ones(2), 0, 2)


if __name__ == '__main__':
    unittest.main()
