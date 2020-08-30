function [Loss] = get_cali_METANET(initial)
Loss = py.calibration.cali_METANET(initial);
end
