# Copyright (c) 2024, Parsimony LLC and contributors
# For license information, please see license.txt

import frappe
import urllib
import requests
from frappe.model.document import Document
from frappe.desk.form.assign_to import add as assign_task
from clickup_integration.constants import (
	GET_TEAMS,
	GET_SPACES,
	GET_FOLDERS,
	GET_TASKS,
	GET_TASK,
	GET_LISTS,
	GET_COMMENTS
)


class ClickupSettings(Document):
	def get_teams(self):
		if not self.get_password("access_token"):
			frappe.throw("No Access token found please authorize.")
		response = requests.get(
			GET_TEAMS,
			headers= {
				"Content-Type": "application/json",
				"Authorization": self.get_password("access_token")
			}
		)
		if response.status_code == 200:
			response = frappe.parse_json(response.content.decode())
			for team in response.get("teams"):
				self.get_spaces(team_id=team.get("id"))

	def get_spaces(self, team_id):
		response = requests.get(
			GET_SPACES.format(team_id=team_id),
			headers= {
				"Content-Type": "application/json",
				"Authorization": self.get_password("access_token")
			}
		)
		if response.status_code == 200:
			response = frappe.parse_json(response.content.decode())
			for space in response.get("spaces"):
				self.get_folders(space_id=space.get("id"))

	def get_folders(self, space_id):
		response = requests.get(
			GET_FOLDERS.format(space_id=space_id),
			headers= {
				"Content-Type": "application/json",
				"Authorization": self.get_password("access_token")
			}
		)
		if response.status_code == 200:
			response = frappe.parse_json(response.content.decode())
			for folder in response.get("folders"):
				project = frappe.db.exists("Project", {"project_name": folder.get("name")})
				if not project:
					project_doc = frappe.new_doc("Project")
					project_doc.update({
						"project_name": folder.get("name")
					})
					project_doc.save()
					project = project_doc.name
					frappe.db.commit()
				self.get_lists(folder_id=folder.get("id"), project=project)

	def get_lists(self, folder_id, project=None):
		response = requests.get(
			GET_LISTS.format(folder_id=folder_id),
			headers= {
				"Content-Type": "application/json",
				"Authorization": self.get_password("access_token")
			}
		)
		if response.status_code == 200:
			response = frappe.parse_json(response.content.decode())
			for list in response.get("lists"):
				self.get_tasks(list_id=list.get("id"), project=project)


	def get_tasks(self, list_id, project):
		response = requests.get(
			GET_TASKS.format(list_id=list_id),
			headers= {
				"Content-Type": "application/json",
				"Authorization": self.get_password("access_token")
			}
		)
		if response.status_code == 200:
			response = frappe.parse_json(response.content.decode())
			for d in response.get("tasks"):
				self.get_task_and_create_task(task_id=d.get("id"), project=project)

	def get_task_and_create_task(self, task_id, project=None):
		response = requests.get(
			GET_TASK.format(task_id=task_id),
			headers= {
				"Content-Type": "application/json",
				"Authorization": self.get_password("access_token")
			},
			params={"include_subtasks": "true"}
		)
		if response.status_code == 200:
			response = frappe.parse_json(response.content.decode())
			existing_task = frappe.db.exists("Task", {"task_id": response.get("id")})
			if existing_task:
				if response.get("attachments"):
					self.attach_files(attachments=response.get("attachments"), task=existing_task)

				self.get_comments(task_id=response.get("id"), task=existing_task)
				return

			task = self.create_task(clickup_task=response, project=project)

	def create_task(self, clickup_task, project):
		task = frappe.new_doc("Task")
		task.update({
			"subject": clickup_task.get("name"),
			"description": clickup_task.get("description"),
			"project": project,
			# "parent_task": parent_task,
			"task_id": clickup_task.get("id"),
			"space_id": clickup_task.get("space").get("id"),
			"list_id": clickup_task.get("list").get("id"),
			"list_name": clickup_task.get("list").get("name"),
			"folder_id": clickup_task.get("folder").get("id"),
			"folder_name": clickup_task.get("folder").get("name")
		})
		task.save()
		frappe.db.commit()

		if clickup_task.get("assignees"):
				self.assign_users(assignees=clickup_task.get("assignees"), task=task.name)

		self.get_comments(task_id=clickup_task.get("id"), task=task.name)

		if clickup_task.get("attachments"):
			self.attach_files(attachments=clickup_task.get("attachments"), task=task.name)

		if clickup_task.get("subtasks"):
			self.create_sub_tasks(subtasks=clickup_task.get("subtasks"), project=project, parent_task=task.name)

		return task.name

	def create_sub_tasks(self, subtasks, project, parent_task):
		for subtask in subtasks:
			existing_task = frappe.db.exists("Task", {"task_id": subtask.get("id")})
			if existing_task:
				if response.get("attachments"):
					self.attach_files(attachments=response.get("attachments"), task=existing_task)
				self.get_comments(task_id=subtask.get("id"), task=existing_task)
				continue

			response = requests.get(
				GET_TASK.format(task_id=subtask.get("id")),
				headers= {
					"Content-Type": "application/json",
					"Authorization": self.get_password("access_token")
				},
			)
			if response.status_code == 200:
				response = frappe.parse_json(response.content.decode())
				task = frappe.new_doc("Task")
				task.update({
					"subject": response.get("name"),
					"description": response.get("description"),
					"project": project,
					"parent_task": parent_task,
					"task_id": response.get("id"),
					"space_id": response.get("space").get("id"),
					"list_id": response.get("list").get("id"),
					"list_name": response.get("list").get("name"),
					"folder_id": response.get("folder").get("id"),
					"folder_name": response.get("folder").get("name")
				})
				task.save()
				frappe.db.commit()

				if response.get("assignees"):
					self.assign_users(assignees=response.get("assignees"), task=task.name)

				self.get_comments(task_id=response.get("id"), task=task.name)

				if response.get("attachments"):
					self.attach_files(attachments=response.get("attachments"), task=task.name)


	def attach_files(self, attachments, task):
		for attachment in attachments:
			if frappe.db.exists("File", {"clickup_attachment_id": attachment.get("id")}):
					continue

			file_response = requests.get(attachment.get("url"))
			if file_response.status_code == 200:
				filename = urllib.parse.unquote(attachment.get("url").split("/")[-1])
				file_doc = frappe.get_doc({
					"doctype": "File",
					"file_name": filename,
					"attached_to_doctype": "Task",
					"content": file_response.content,
					"attached_to_name": task,
					"clickup_attachment_id": attachment.get("id")
				})
				file_doc.save()

	def assign_users(self, assignees, task):
		for assignee in assignees:
			if frappe.db.exists("User", {"email": assignee.get("email"), "enabled": 1}):
				assign_task({
					"assign_to": [assignee.get("email")],
					"doctype": "Task",
					"name": task
				})

	def get_comments(self, task_id, task):
		response = requests.get(
			GET_COMMENTS.format(task_id=task_id),
			headers= {
				"Content-Type": "application/json",
				"Authorization": self.get_password("access_token")
			}
		)
		if response.status_code == 200:
			comments = frappe.parse_json(response.content.decode())
			for comment in comments.get("comments"):
				if frappe.db.exists("Comment", {"clickup_comment_id": comment.get("id")}):
					continue
				user = comment.get("user").get("email")
				username = comment.get("user").get("username")

				if frappe.db.exists("User", {"email": user, "enabled": 1}):
					frappe.session.user = user
					comment_content = comment.get("comment_text")
				else:
					comment_content = f"Commented By - {username} ({user}) <br>" +  comment.get("comment_text")

				comment_doc = frappe.new_doc("Comment")
				comment_doc.update({
					"doctype": "Comment",
					"comment_type": "Comment",
					"comment_email": user,
					"comment_by": user,
					"reference_doctype": "Task",
					"reference_name": task,
					"content": comment_content,
					"clickup_comment_id": comment.get("id")
				})
				comment_doc.save(ignore_permissions=True)
				frappe.session.user = "Administrator"

@frappe.whitelist()
def sync_tasks():
	frappe.enqueue_doc(
		"Clickup Settings",
		"Clickup Settings",
		"get_teams",
		queue="long",
		timeout=3600,
	)
	return True