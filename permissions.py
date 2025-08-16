PERMISSIONS = {
    "QC Officer": ["view_qc", "add_qc_data"],
    "Junior Officer": ["view_qc"],
    "Senior Officer": ["view_qc", "add_qc_data", "approve_qc_data"],
    "Executive": ["view_qc", "add_qc_data", "edit_qc_data"],
    "Senior Executive": ["view_qc", "add_qc_data", "edit_qc_data", "approve_qc_data"],
    "Assistant Manager": ["view_qc", "add_qc_data", "edit_qc_data", "approve_qc_data", "delete_qc_data"],
    "HOD": ["view_qc", "add_qc_data", "edit_qc_data", "approve_qc_data", "delete_qc_data", "manage_users"],

    "Production Officer": ["view_production", "add_production_data"],
    "Production Manager": ["view_production", "add_production_data", "approve_production_data"],

    "Warehouse Officer": ["view_warehouse", "add_warehouse_data"],
    "Warehouse Manager": ["view_warehouse", "add_warehouse_data", "approve_warehouse_data"],

    "QA Officer": ["view_qa", "add_qa_data"],
    "QA Manager": ["view_qa", "add_qa_data", "approve_qa_data"]
}

def has_permission(user_role, action):
    """
    Check if the given role has permission for a specific action.
    """
    return action in PERMISSIONS.get(user_role, [])
