from django.contrib import admin
from .models import Department, Employee, Attendance, LeaveRequest, Notice, TaskAttachment, TaskFeedback

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'department', 'email', 'monthly_salary', 'position')
    search_fields = ('employee_id', 'first_name', 'last_name', 'email')
    list_filter = ('department', 'position')
    readonly_fields = ('dob_nepali',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'employee_id', 'first_name', 'last_name', 'email', 'position', 'department')
        }),
        ('Personal Details', {
            'fields': ('dob', 'dob_nepali', 'address', 'photo')
        }),
        ('Banking Information', {
            'fields': ('monthly_salary', 'bank_name', 'bank_account_number', 'bank_account_holder_name')
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'check_in', 'check_out', 'hours_worked', 'status', 'has_tasks', 'has_feedback_display')
    list_filter = ('date', 'status', 'employee')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    readonly_fields = ('hours_worked',)
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Employee & Date', {
            'fields': ('employee', 'date', 'status')
        }),
        ('Time Tracking', {
            'fields': ('check_in', 'check_out', 'hours_worked')
        }),
        ('Tasks', {
            'fields': ('todo_tasks', 'completed_tasks'),
            'classes': ('collapse',)
        }),
        ('Comments', {
            'fields': ('comments',),
            'classes': ('collapse',)
        }),
    )
    
    def has_tasks(self, obj):
        """Show if attendance has tasks"""
        return bool(obj.todo_tasks or obj.completed_tasks)
    has_tasks.boolean = True
    has_tasks.short_description = 'Has Tasks'
    
    def has_feedback_display(self, obj):
        """Show if admin has provided feedback"""
        if obj.has_feedback():
            if obj.task_feedback.approved:
                return "✅ Approved"
            else:
                return "⚠️ Reviewed"
        return "-"
    has_feedback_display.short_description = 'Feedback Status'


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'title', 'start_date', 'end_date', 'status', 'created_at')
    list_filter = ('status', 'start_date', 'end_date', 'employee')
    search_fields = ('employee__first_name', 'employee__last_name', 'title', 'remarks')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee',)
        }),
        ('Leave Details', {
            'fields': ('title', 'remarks', 'start_date', 'end_date', 'status')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at',)


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'is_active', 'published_at', 'created_by', 'is_new_display')
    list_filter = ('is_active', 'priority', 'published_at')
    search_fields = ('title', 'description')
    date_hierarchy = 'published_at'
    
    fieldsets = (
        ('Notice Content', {
            'fields': ('title', 'description', 'priority')
        }),
        ('Publishing', {
            'fields': ('is_active', 'published_at')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at',)
    
    def is_new_display(self, obj):
        """Display if notice is new (< 24 hours)"""
        return obj.is_new
    is_new_display.boolean = True
    is_new_display.short_description = 'New?'
    
    def save_model(self, request, obj, form, change):
        """Automatically set created_by to current user"""
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ('attendance', 'task_type', 'uploaded_at', 'caption', 'image_preview')
    list_filter = ('task_type', 'uploaded_at')
    search_fields = ('attendance__employee__first_name', 'attendance__employee__last_name', 'caption')
    date_hierarchy = 'uploaded_at'
    readonly_fields = ('uploaded_at', 'image_preview')
    
    fieldsets = (
        ('Attachment Information', {
            'fields': ('attendance', 'task_type', 'image', 'image_preview', 'caption')
        }),
        ('Metadata', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        """Display image preview in admin"""
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-width: 200px; max-height: 200px;" />'
        return "-"
    image_preview.allow_tags = True
    image_preview.short_description = 'Preview'


@admin.register(TaskFeedback)
class TaskFeedbackAdmin(admin.ModelAdmin):
    list_display = ('attendance', 'employee_name', 'date', 'approved', 'reviewed_by', 'reviewed_at', 'is_read')
    list_filter = ('approved', 'is_read', 'reviewed_at', 'attendance__employee')
    search_fields = ('attendance__employee__first_name', 'attendance__employee__last_name', 'admin_comment')
    date_hierarchy = 'reviewed_at'
    readonly_fields = ('reviewed_at',)
    
    fieldsets = (
        ('Feedback Details', {
            'fields': ('attendance', 'approved', 'admin_comment')
        }),
        ('Review Information', {
            'fields': ('reviewed_by', 'reviewed_at', 'is_read')
        }),
    )
    
    def employee_name(self, obj):
        """Display employee name"""
        return f"{obj.attendance.employee.first_name} {obj.attendance.employee.last_name}"
    employee_name.short_description = 'Employee'
    employee_name.admin_order_field = 'attendance__employee__first_name'
    
    def date(self, obj):
        """Display attendance date"""
        return obj.attendance.date
    date.short_description = 'Date'
    date.admin_order_field = 'attendance__date'
    
    def save_model(self, request, obj, form, change):
        """Automatically set reviewed_by and reviewed_at"""
        if not change:  # Only on creation
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


# Optional: Inline admin for related models
class TaskAttachmentInline(admin.TabularInline):
    model = TaskAttachment
    extra = 0
    readonly_fields = ('uploaded_at',)
    fields = ('task_type', 'image', 'caption', 'uploaded_at')


class TaskFeedbackInline(admin.StackedInline):
    model = TaskFeedback
    extra = 0
    readonly_fields = ('reviewed_at',)
    fields = ('approved', 'admin_comment', 'reviewed_by', 'reviewed_at', 'is_read')
    
    def get_readonly_fields(self, request, obj=None):
        """Make reviewed_by readonly after creation"""
        if obj and obj.task_feedback:
            return self.readonly_fields + ('reviewed_by',)
        return self.readonly_fields


# Optional: Add inlines to Attendance admin
# Uncomment the lines below to add inline editing
# class AttendanceAdminWithInlines(AttendanceAdmin):
#     inlines = [TaskAttachmentInline, TaskFeedbackInline]