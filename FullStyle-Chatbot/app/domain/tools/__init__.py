# Import all tools
from app.domain.tools.additional_utils.get_worker import GetWorkersTool
from app.domain.tools.additional_utils.get_worker_has_service import (
    GetWorkerHasServiceTool,
)
from app.domain.tools.appointment_management.delete_appointment import (
    DeleteAppointmentTool,
)
from app.domain.tools.appointment_management.get_appointment import GetAppointmentTool
from app.domain.tools.appointment_management.get_appointmentdetail import (
    GetAppointmentDetailTool,
)
from app.domain.tools.appointment_management.post_appointment import PostAppointmentTool
from app.domain.tools.appointment_management.put_appointment import PutAppointmentTool
from app.domain.tools.appointment_management.validate_appointment import (
    ValidateAppointmentTool,
)
from app.domain.tools.site_and_services.get_category import GetCategoryTool
from app.domain.tools.site_and_services.get_detail import GetDetailTool
from app.domain.tools.site_and_services.get_service import GetServicesTool
from app.domain.tools.site_and_services.get_site import GetSitesTool
from app.domain.tools.site_and_services.get_site_has_category import (
    GetSiteHasCategoryTool,
)
from app.domain.tools.time_and_schedule.get_availability import GetAvailabilityTool
from app.domain.tools.time_and_schedule.get_worker_daily_schedule import (
    GetWorkerDailyScheduleTool,
)
from app.domain.tools.time_and_schedule.get_worker_weekly_schedule import (
    GetWorkerWeeklyScheduleTool,
)

# List of all tools to be used by the Langchain agent
all_tools = [
    GetWorkerHasServiceTool(),
    GetWorkersTool(),
    DeleteAppointmentTool(),
    GetAppointmentTool(),
    GetAppointmentDetailTool(),
    PostAppointmentTool(),
    PutAppointmentTool(),
    ValidateAppointmentTool(),
    GetCategoryTool(),
    GetDetailTool(),
    GetServicesTool(),
    GetSiteHasCategoryTool(),
    GetSitesTool(),
    GetAvailabilityTool(),
    GetWorkerDailyScheduleTool(),
    GetWorkerWeeklyScheduleTool(),
]
