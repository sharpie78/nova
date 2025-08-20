export function renderGeneralSettings(container, currentSettings) {
  const title = document.createElement("h2");
  title.textContent = "General Settings";
  title.classList.add("settings-title");

  const spacer = document.createElement("div");
  spacer.style.height = "2.4rem";
  container.appendChild(title);
  container.appendChild(spacer);

  const usernameFromStorage = localStorage.getItem("username");
  const role = currentSettings?.general?.role?.default;

  if (role === 'Admin') {
    // USERS
    const usersTitle = document.createElement('h3');
    usersTitle.textContent = 'Users';
    container.appendChild(usersTitle);

    const usernameDropdown = document.createElement('select');
    usernameDropdown.id = 'username-dropdown';
    usernameDropdown.classList.add('dark-select');

    const usernameWrapper = document.createElement('div');
    usernameWrapper.classList.add('select-wrapper');
    usernameWrapper.appendChild(usernameDropdown);
    const userArrow = document.createElement('span');
    userArrow.className = "material-symbols-outlined dropdown-icon";
    userArrow.textContent = "expand_more";
    usernameWrapper.appendChild(userArrow);
    container.appendChild(usernameWrapper);

    fetch("http://127.0.0.1:56969/users")
      .then(res => res.json())
      .then(users => {
        users.forEach(user => {
          if (user.username !== 'admin') {
            const opt = document.createElement('option');
            opt.value = user.username;
            opt.textContent = user.username;
            usernameDropdown.appendChild(opt);
          }
        });
      })
      .catch(err => console.error("Error fetching users:", err));

    // ROLE
    const roleTitle = document.createElement('h3');
    roleTitle.textContent = 'Role';
    container.appendChild(roleTitle);

    const roleDropdown = document.createElement('select');
    roleDropdown.id = 'role-dropdown';
    roleDropdown.disabled = true;
    roleDropdown.classList.add('dark-select');

    const roleWrapper = document.createElement('div');
    roleWrapper.classList.add('select-wrapper');
    roleWrapper.appendChild(roleDropdown);
    const roleArrow = document.createElement('span');
    roleArrow.className = "material-symbols-outlined dropdown-icon";
    roleArrow.textContent = "expand_more";
    roleWrapper.appendChild(roleArrow);
    container.appendChild(roleWrapper);

    ['Admin', 'User'].forEach(role => {
      const opt = document.createElement('option');
      opt.value = role.toLowerCase();
      opt.textContent = role;
      roleDropdown.appendChild(opt);
    });

    usernameDropdown.addEventListener('change', () => {
      const selectedUsername = usernameDropdown.value;
      fetch("http://127.0.0.1:56969/users")
        .then(res => res.json())
        .then(users => {
          const selectedUser = users.find(u => u.username === selectedUsername);
          if (selectedUser) {
            roleDropdown.value = selectedUser.role;
            roleDropdown.disabled = selectedUser.role === 'admin';
          }
        });
    });


    const saveRoleButton = document.createElement('button');
    saveRoleButton.textContent = "Save Role";
    saveRoleButton.addEventListener('click', () => {
      fetch(`http://127.0.0.1:56969/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: usernameDropdown.value,
          role: roleDropdown.value
        })
      })
        .then(res => {
          if (res.ok) alert('Role updated successfully!');
          else alert('Failed to update role.');
        })
        .catch(err => console.error("Error updating role:", err));
    });

    const buttonWrapper = document.createElement('div');
    buttonWrapper.style.display = 'inline-block';
    buttonWrapper.appendChild(saveRoleButton);
    container.appendChild(buttonWrapper);

    // DELETE USER
    if (currentSettings.general.delete_user) {
      const deleteTitle = document.createElement('h3');
      deleteTitle.textContent = currentSettings.general.delete_user.label;
      container.appendChild(deleteTitle);

      const deleteDropdown = document.createElement('select');
      deleteDropdown.id = 'delete-user-dropdown';
      deleteDropdown.classList.add('dark-select');

      const deleteWrapper = document.createElement('div');
      deleteWrapper.classList.add('select-wrapper');
      deleteWrapper.appendChild(deleteDropdown);
      const deleteArrow = document.createElement('span');
      deleteArrow.className = "material-symbols-outlined dropdown-icon";
      deleteArrow.textContent = "expand_more";
      deleteWrapper.appendChild(deleteArrow);
      container.appendChild(deleteWrapper);

      fetch("http://127.0.0.1:56969/users")
        .then(res => res.json())
        .then(users => {
          users.forEach(user => {
            if (user.username !== 'admin') {
              const opt = document.createElement('option');
              opt.value = user.username;
              opt.textContent = user.username;
              deleteDropdown.appendChild(opt);
            }
          });
        })
        .catch(err => console.error("Error fetching users:", err));

      const deleteBtn = document.createElement('button');
      deleteBtn.id = "delete-user";
      deleteBtn.textContent = "Delete User";
      deleteBtn.classList.add("settings-delete-button");
      deleteBtn.style.marginTop = "12px";

      deleteBtn.onclick = () => {
        const selectedUser = deleteDropdown.value;
        if (!selectedUser) return;

        if (!confirm(`Are you sure you want to delete user "${selectedUser}"?`)) return;

        fetch(`http://127.0.0.1:56969/users/${selectedUser}`, {
          method: 'DELETE'
        })
          .then(res => {
            if (res.ok) {
              alert(`User "${selectedUser}" deleted.`);
              location.reload();
            } else {
              alert("Failed to delete user.");
            }
          })
          .catch(err => {
            console.error("Error deleting user:", err);
            alert("Error occurred while deleting.");
          });
      };

      container.appendChild(deleteBtn);
    }

  } else {
    const label = document.createElement("label");
    label.textContent = "User name";
    const input = document.createElement("input");
    input.type = "text";
    input.value = usernameFromStorage;
    input.readOnly = true;
    container.appendChild(label);
    container.appendChild(input);
  }
}
