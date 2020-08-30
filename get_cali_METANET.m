function [Loss] = get_cali_METANET(initial)
Loss = py.calibration_mat.cali_METANET(initial);
end