from scripts.cp_f_delivery_replay import business_result_projection, linear_quantile

def test_business_result_projection_ignores_trial_identity_only():
    first={"trial_id":1,"final_cash":500,"final_net_project_equity":700,"partner1_final_entitlement":400}
    second={"trial_id":2,"final_cash":500,"final_net_project_equity":700,"partner1_final_entitlement":400}
    assert business_result_projection(first)==business_result_projection(second)
    second["final_cash"]=501
    assert business_result_projection(first)!=business_result_projection(second)

def test_linear_quantile_preserves_interpolated_integer_metric_values():
    assert linear_quantile([0,1],0.25)==0.25
    assert linear_quantile([1,3,5],0.50)==3.0

def test_linear_quantile_supports_negative_currency_values():
    assert linear_quantile([-9,-3,3,9],0.25)==-4.5
