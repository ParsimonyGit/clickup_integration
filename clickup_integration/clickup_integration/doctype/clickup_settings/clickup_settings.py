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
				task_name = frappe.db.exists("Task", {"is_group": 1, "subject": space.get("name")})
				if not task_name:
					task_doc = frappe.new_doc("Task")
					task_doc.update({
						"subject": space.get("name"),
						"is_group": 1,
						"space_id": space.get("id"),
						"space_name": space.get("name")
					})
					task_doc.save()
					task_name = task_doc.name
					frappe.db.commit()
				self.get_folders(space_id=space.get("id"), parent_task=task_name)

	def get_folders(self, space_id, parent_task=None):
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
				self.get_lists(folder_id=folder.get("id"), project=project, parent_task=parent_task)

	def get_lists(self, folder_id, project=None, parent_task=None):
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
				self.get_tasks(list_id=list.get("id"), project=project, parent_task=parent_task)


	def get_tasks(self, list_id, project, parent_task):
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
				self.get_task_and_create_task(task_id=d.get("id"), project=project, parent_task=parent_task)

	def get_task_and_create_task(self, task_id, project=None, parent_task=None):
		response = requests.get(
			GET_TASK.format(task_id=task_id),
			headers= {
				"Content-Type": "application/json",
				"Authorization": self.get_password("access_token")
			}
		)
		if response.status_code == 200:
			response = frappe.parse_json(response.content.decode())
			existing_task = frappe.db.exists("Task", {"task_id": response.get("id")})
			if existing_task:
				for attachment in response.get("attachments"):
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
							"attached_to_name": existing_task,
							"clickup_attachment_id": attachment.get("id")
						})
						file_doc.save()

				self.get_comments(task_id=response.get("id"), task=existing_task)
				return

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
			for assignee in response.get("assignees"):
				if frappe.db.exists("User", {"email": assignee.get("email"), "enabled": 1}):
					assign_task({
						"assign_to": [assignee.get("email")],
						"doctype": "Task",
						"name": task.name
					})
			self.get_comments(task_id=response.get("id"), task=task.name)
			for attachment in response.get("attachments"):
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
						"attached_to_name": task.name,
						"clickup_attachment_id": attachment.get("id")
					})
					file_doc.save()
		frappe.db.commit()

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
					comment_content = f"Commented By - {username}({user}) <br>" +  comment.get("comment_text")

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