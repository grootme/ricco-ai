# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors

import frappe

from gameplan.gameplan.doctype.gp_unread_record.gp_unread_record import GPUnreadRecord


class UnreadRecordsMigrator:
	"""Migrates existing discussion visits to unread records system."""

	def __init__(self):
		self.discussion_project = {}
		self.user_discussion_visits = {}
		self.discussion_comments = {}
		self.user_project_visits = {}

	def execute(self):
		"""Main execution method for the migration."""
		self._load_data()

		all_projects = frappe.get_all("GP Project", fields=["name"], pluck="name")
		total_projects = len(all_projects)

		for idx, project_name in enumerate(all_projects):
			project_name_str = str(project_name)
			project_members = GPUnreadRecord._get_project_members(project_name_str)
			unread_records = []

			for user in project_members:
				user_records = self._generate_unread_records_for_user_in_project(user, project_name_str)
				unread_records.extend(user_records)

			if unread_records:
				GPUnreadRecord._bulk_create_unread_records(unread_records)

			frappe.utils.update_progress_bar("Creating unread records", idx + 1, total_projects)

	def _load_data(self):
		"""Load all required data from database."""
		self._load_discussion_visits()
		self._load_discussions()
		self._load_comments()
		self._load_project_visits()

	def _load_discussion_visits(self):
		"""Load discussion visit records."""
		discussion_visits = frappe.qb.get_query(
			"GP Discussion Visit",
			fields=["name", "user", "discussion", "last_visit"],
		).run(as_dict=1)

		for visit in discussion_visits:
			key = (visit.user, str(visit.discussion))
			self.user_discussion_visits[key] = visit

	def _load_discussions(self):
		"""Load all discussions."""
		self.all_discussions = frappe.qb.get_query(
			"GP Discussion", fields=["name", "project", "owner", "creation", "last_post_at"]
		).run(as_dict=1)

		for discussion in self.all_discussions:
			self.discussion_project[str(discussion.name)] = discussion.project

	def _load_comments(self):
		"""Load comments and group by discussion."""
		all_comments = frappe.qb.get_query(
			"GP Comment",
			fields=["name", "reference_name as discussion", "owner", "creation"],
			filters={"reference_doctype": "GP Discussion"},
		).run(as_dict=1)

		for comment in all_comments:
			self.discussion_comments.setdefault(comment.discussion, []).append(comment)

	def _load_project_visits(self):
		"""Load project visit records."""
		project_visits = frappe.qb.get_query(
			"GP Project Visit",
			fields=["user", "project", "mark_all_read_at"],
			filters={"mark_all_read_at": ["is", "set"]},
		).run(as_dict=1)

		for visit in project_visits:
			key = (visit.user, visit.project)
			self.user_project_visits[key] = visit

	def _generate_unread_records_for_user_in_project(self, user, project_name):
		"""Generate unread records for a specific user in a specific project."""
		unread_records = []
		discussion_counts = 0
		comment_counts = 0

		project_discussions = [d for d in self.all_discussions if d.project == project_name]

		for discussion in project_discussions:
			if not self._should_process_discussion(user, discussion):
				continue

			last_timestamp = self._get_last_read_timestamp(user, discussion)

			if last_timestamp is None:
				discussion_record, comment_records = self._create_records_for_unvisited_discussion(
					user, discussion
				)
				unread_records.append(discussion_record)
				unread_records.extend(comment_records)
				discussion_counts += 1
				comment_counts += len(comment_records)
			else:
				comment_records = self._create_records_for_unread_comments(user, discussion, last_timestamp)
				unread_records.extend(comment_records)
				comment_counts += len(comment_records)

		return unread_records

	def _should_process_discussion(self, user, discussion):
		"""Check if discussion should be processed for the user."""
		return discussion.owner != user

	def _get_last_read_timestamp(self, user, discussion):
		"""Get the last timestamp when the user read the discussion."""
		key = (user, str(discussion.name))
		visit = self.user_discussion_visits.get(key)
		last_visit_timestamp = visit.last_visit if visit else None

		project_visit = self.user_project_visits.get((user, discussion.project))
		if project_visit and project_visit.mark_all_read_at:
			if discussion.creation <= project_visit.mark_all_read_at:
				return discussion.creation

		mark_all_as_read_timestamp = project_visit.mark_all_read_at if project_visit else None

		return (
			max(last_visit_timestamp, mark_all_as_read_timestamp)
			if last_visit_timestamp and mark_all_as_read_timestamp
			else last_visit_timestamp or mark_all_as_read_timestamp
		)

	def _create_records_for_unvisited_discussion(self, user, discussion):
		"""Create unread records for a discussion that was never visited."""
		discussion_record = self._create_unread_record(
			user=user, discussion=discussion, creation=discussion.creation, owner=discussion.owner
		)

		comment_records = []
		comments = self.discussion_comments.get(str(discussion.name), [])

		for comment in comments:
			if comment.owner != user:
				comment_record = self._create_unread_record(
					user=user,
					discussion=discussion,
					comment=comment,
					creation=comment.creation,
					owner=comment.owner,
				)
				comment_records.append(comment_record)

		return discussion_record, comment_records

	def _create_records_for_unread_comments(self, user, discussion, last_timestamp):
		"""Create unread records for comments that are unread."""
		comment_records = []
		comments = self.discussion_comments.get(str(discussion.name), [])

		for comment in comments:
			if comment.owner != user and comment.creation > last_timestamp:
				comment_record = self._create_unread_record(
					user=user,
					discussion=discussion,
					comment=comment,
					creation=comment.creation,
					owner=comment.owner,
				)
				comment_records.append(comment_record)

		return comment_records

	def _create_unread_record(self, user, discussion, comment=None, creation=None, owner=None):
		"""Create a single unread record."""
		record_data = {
			"doctype": "GP Unread Record",
			"name": frappe.db.get_next_sequence_val("GP Unread Record"),
			"user": user,
			"discussion": str(discussion.name),
			"project": str(discussion.project),
			"is_unread": 1,
			"creation": creation,
			"modified": creation,
			"owner": owner,
		}

		if comment:
			record_data["comment"] = str(comment.name)

		return frappe.get_doc(record_data)


def execute():
	"""Migrate existing discussion visits to unread records system."""

	migrator = UnreadRecordsMigrator()
	migrator.execute()
