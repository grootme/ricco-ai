# Unread Count Refactor Plan

## 🎉 IMPLEMENTATION STATUS: PHASE 1-6 COMPLETED ✅

### 📋 Summary of Completed Work

**✅ Backend Implementation Complete**: All core backend functionality has been successfully implemented with v2 functions running alongside the existing system for seamless migration.

**✅ Migration Ready**: Comprehensive data migration script created to move existing unread tracking data from the old system to the new GP Unread Record system.

**📍 Current Status**: The migration script has been enhanced to process all projects for all users, with comprehensive access control, bulk insert optimization, and user-aware unread logic. The system is ready for migration testing.

**Next Steps**:
1. **Test the migration script** in a development environment to validate data integrity
2. Update frontend components to use new unread count API endpoints
3. Performance validation and system testing

## Overview
Refactor the current unread count system from GP Discussion Visit and GP Project Visit based tracking to a new GP Unread Record based system for improved performance and accuracy.

## Current System Analysis

### Current DocTypes and Their Usage

1. **GP Discussion Visit** (`gameplan/gameplan/doctype/gp_discussion_visit/`)
   - **Purpose**: Tracks when a user last visited a discussion
   - **Fields**: `user`, `discussion`, `last_visit`
   - **Current Usage**: Used to determine if a discussion is unread by comparing `last_visit` with `discussion.last_post_at`
   - **Performance Issue**: Requires complex JOINs and timestamp comparisons

2. **GP Project Visit** (`gameplan/gameplan/doctype/gp_project_visit/`)
   - **Purpose**: Tracks when a user last visited a project and "mark all as read" timestamps
   - **Fields**: `user`, `project`, `team`, `last_visit`, `mark_all_read_at`
   - **Current Usage**: Used for project-level "mark all as read" functionality
   - **Performance Issue**: Complex logic in `get_unread_count()` function

### Current Implementation Files

1. **Main Unread Count Logic**
   - File: `gameplan/gameplan/doctype/gp_project/gp_project.py`
     - Function: `get_unread_count()`
   - File: `gameplan/gameplan/doctype/gp_discussion/api.py`
     - Function: `get_discussions()`

2. **Discussion Visit Tracking**
   - File: `gameplan/gameplan/doctype/gp_discussion/gp_discussion.py`
   - Method: `track_visit()`

3. **Project Visit Tracking**
   - File: `gameplan/gameplan/doctype/gp_project/gp_project.py`
   - Methods: `track_visit()`, `mark_all_as_read()`

## New System Design

### GP Unread Record DocType
**Location**: `gameplan/gameplan/doctype/gp_unread_record/` (already created)

**Fields**:
- `user` (Link to User)
- `discussion` (Link to GP Discussion)
- `comment` (Link to GP Comment) - nullable for discussion itself
- `project` (Link to GP Project)
- `is_unread` (Check - default 1)

**Indexes Required**:
- `user, discussion, is_unread` (for per-discussion unread count)
- `user, project, is_unread` (for per-project unread count)
- `user, is_unread` (for total unread count)

### New Logic Flow

1. **When a discussion is created**:
   - Create one unread record for every user in the project with `comment=NULL`

2. **When a comment is created**:
   - Create one unread record for every user in the project linking to that comment

3. **When a user visits a discussion**:
   - Update all unread records for that user and discussion to `is_unread=0`

4. **Unread count calculation**:
   - Discussion level: `COUNT(*) WHERE user=X AND discussion=Y AND is_unread=1`
   - Project level: `COUNT(*) WHERE user=X AND project=Y AND is_unread=1`
   - Total: `COUNT(*) WHERE user=X AND is_unread=1`

## Implementation Plan

### Phase 1: Core DocType Implementation ✅ COMPLETED

#### 1.1 Update GP Unread Record DocType ✅ COMPLETED
**File**: `gameplan/gameplan/doctype/gp_unread_record/gp_unread_record.json`
- ✅ Already created with correct fields
- ✅ **COMPLETED**: Fixed default value for `is_unread` field from "0" to "1"

**File**: `gameplan/gameplan/doctype/gp_unread_record/gp_unread_record.py`
- ✅ **COMPLETED**: Created Python controller class with static methods
- **Static Methods implemented**:
  - `create_unread_records_for_discussion(discussion_name)` - Create unread records for all project members when discussion is created
  - `create_unread_records_for_comment(comment_doc)` - Create unread records for all project members when comment is created
  - `mark_discussion_as_read_for_user(discussion_name, user)` - Mark all unread records for this discussion and user as read
  - `mark_all_as_read_for_project(project_name, user)` - Mark all discussions in project as read for user
  - `get_unread_count_by_project(user)` - Get unread count per project for user
  - `get_total_unread_count(user)` - Get total unread count for user
  - `get_discussion_unread_count(user, discussion_name)` - Get unread count for specific discussion
  - `after_doctype_insert()` - Add database indexes

#### 1.2 Add Database Indexes ✅ COMPLETED
**File**: `gameplan/gameplan/doctype/gp_unread_record/patches/add_indexes.py`
- ✅ **COMPLETED**: Created patch to add required indexes
- ✅ **COMPLETED**: Added patch entry to `gameplan/patches.txt`: `gameplan.gameplan.doctype.gp_unread_record.patches.add_indexes`
- **Indexes added**:
  - `user_discussion_unread`: ["user", "discussion", "is_unread"]
  - `user_project_unread`: ["user", "project", "is_unread"]
  - `user_unread`: ["user", "is_unread"]

### Phase 2: Create Unread Records ✅ COMPLETED

#### 2.1 Update GP Discussion Controller ✅ COMPLETED
**File**: `gameplan/gameplan/doctype/gp_discussion/gp_discussion.py`

**Actions**:
1. ✅ **COMPLETED**: Imported GP Unread Record controller
2. ✅ **COMPLETED**: Updated `after_insert()` to call static method for creating unread records
3. ✅ **COMPLETED**: Updated `track_visit()` to mark as read in new system (while keeping old system for backward compatibility)

#### 2.2 Update GP Comment Controller ✅ COMPLETED
**File**: `gameplan/gameplan/doctype/gp_comment/gp_comment.py`

**Actions**:
1. ✅ **COMPLETED**: Imported GP Unread Record controller
2. ✅ **COMPLETED**: Updated `after_insert()` to call static method for creating unread records

### Phase 3: New Unread Count Functions ✅ COMPLETED

#### 3.1 Add New GP Project Unread Count Functions ✅ COMPLETED
**File**: `gameplan/gameplan/doctype/gp_project/gp_project.py`

**Actions**:
1. ✅ **COMPLETED**: Imported GP Unread Record controller
2. ✅ **COMPLETED**: Created new `mark_all_as_read_v2()` method alongside existing one
3. ✅ **COMPLETED**: Created new `get_unread_count_v2()` function alongside existing one
4. ✅ **COMPLETED**: Kept existing functions for backward compatibility

### Phase 4: Update Discussion Visit Tracking ✅ COMPLETED

#### 4.1 Update GP Discussion track_visit Method ✅ COMPLETED
**File**: `gameplan/gameplan/doctype/gp_discussion/gp_discussion.py`

**Actions**:
1. ✅ **COMPLETED**: Updated `track_visit()` method to use new system
2. ✅ **COMPLETED**: Kept creating GP Discussion Visit records for analytics/backward compatibility

### Phase 5: Frontend Updates 🔄 READY FOR IMPLEMENTATION

#### 5.1 Update Frontend API Calls 📋 IDENTIFIED
**Analysis Completed**: Located frontend files that need updates:

**Files identified for future update**:
- ✅ **ANALYZED**: `frontend/src/data/spaces.ts` - Main API call for `get_unread_count`
- ✅ **ANALYZED**: `frontend/src/components/SpaceOptions.vue` - Individual space `mark_all_as_read` call
- ✅ **ANALYZED**: Various Vue components using `getSpaceUnreadCount()` function

**Action Items for Future Implementation**:
1. 🔮 **Future**: Update API calls from `get_unread_count()` to `get_unread_count_v2()`
2. 🔮 **Future**: Update calls from `mark_all_as_read()` to `mark_all_as_read_v2()`
3. 🔮 **Future**: Test all unread count displays in UI with new functions

**Note**: Frontend changes should be implemented after thorough backend testing and data migration.

### Phase 6: Migration and Data Population ✅ COMPLETED

#### 6.1 Create Migration Script ✅ COMPLETED
**File**: `gameplan/patches/migrate_to_unread_records.py`

**Actions**:
1. ✅ **COMPLETED**: Created comprehensive migration script to populate GP Unread Record table from existing data
2. ✅ **COMPLETED**: Handles existing GP Discussion Visit and GP Project Visit data correctly
3. ✅ **COMPLETED**: Added patch entry to `gameplan/patches.txt`: `gameplan.patches.migrate_to_unread_records`

**Migration Features Implemented**:
- ✅ **Correct Privacy Logic**: For private projects, creates records only for project members; for public projects, creates records for all users
- ✅ **Project-Centric Processing**: Iterates by project rather than by user, ensuring efficient access control
- ✅ **Bulk Insert Optimization**: Uses Frappe's `bulk_insert` for efficient database operations
- ✅ **Deduplication**: Built-in duplicate handling via `bulk_insert` without need for fallback logic
- ✅ **User-Aware Logic**: Considers content ownership when determining unread status
- ✅ **Memory Management**: Commits after each project to prevent memory issues
- ✅ **Progress Tracking**: Detailed console output for monitoring migration progress with privacy status
- ✅ **Handles existing visit tracking data correctly**: Accounts for discussion visits and project-level "mark all as read" timestamps
- ✅ **Creates records for both discussions and individual comments**

### Migration Processing Logic
The migration script uses **project-centric processing** with correct privacy handling:

1. **Project Iteration**: Process each project individually with its privacy status
2. **User Selection Logic**:
   - **Private Projects**: Create unread records only for project members
   - **Public Projects**: Create unread records for all users with Gameplan access
3. **Bulk Processing**: For each user in each project, bulk insert all their unread records for that project
4. **Memory Management**: Commit after each project completion to manage memory efficiently

This approach ensures optimal access control and prevents unnecessary record creation.

### Phase 7: Performance Optimization 🔮 FUTURE

#### 7.1 Cleanup Old System (Optional) 🔮 FUTURE
**Actions**:
1. 🔮 **Future**: After thorough testing, gradually replace calls to old functions with v2 functions
2. 🔮 **Future**: Eventually remove old `get_unread_count()` and `mark_all_as_read()` functions
3. 🔮 **Future**: Rename v2 functions to original names once migration is complete
4. 🔮 **Future**: Keep GP Discussion Visit and GP Project Visit for other use cases
5. 🔮 **Future**: Add feature flag to switch between systems during transition (if needed)

#### 7.2 Add Bulk Operations 🔮 FUTURE
**File**: `gameplan/gameplan/doctype/gp_unread_record/utils.py`

**Actions**:
1. 🔮 **Future**: Create utility functions for bulk insert/update operations
2. 🔮 **Future**: Optimize for large datasets

## File Structure Summary

### New Files to Create:
```
gameplan/gameplan/doctype/gp_unread_record/
├── gp_unread_record.py (controller)
├── utils.py (utility functions)
└── patches/
    └── add_indexes.py

gameplan/patches/
└── migrate_to_unread_records.py
```

### Files to Modify:
```
gameplan/gameplan/doctype/gp_unread_record/gp_unread_record.py (static methods)
gameplan/gameplan/doctype/gp_discussion/gp_discussion.py (import and call static methods)
gameplan/gameplan/doctype/gp_comment/gp_comment.py (import and call static methods)
gameplan/gameplan/doctype/gp_project/gp_project.py (add v2 functions alongside existing)
frontend/src/**/*.vue (update API calls to use v2 functions)
```

## Migration Strategy Benefits

### V2 Functions Approach
By creating `get_unread_count_v2()` and `mark_all_as_read_v2()` functions instead of replacing existing ones:

**Advantages**:
1. **Zero Downtime**: Existing functionality continues to work during migration
2. **Gradual Testing**: Can test new system in parallel with production system
3. **Easy Rollback**: Can quickly switch back to old functions if issues are found
4. **Flexible Timeline**: Can migrate different parts of the frontend at different speeds
5. **Performance Comparison**: Can compare old vs new system performance side-by-side

**Migration Path**:
1. [ ] Deploy v2 functions to production
2. [ ] Update frontend components one by one to use v2 functions
3. [ ] Monitor performance and fix any issues
4. [ ] Once all components use v2 functions, remove old functions
5. [ ] Rename v2 functions to original names
