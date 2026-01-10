"""
Gerenciador de usuários com armazenamento em JSON.
Implementa autenticação simples e segura sem banco de dados.
"""

import json
import hashlib
import os
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

from django.conf import settings


class UserManager:
    """
    Gerencia usuários armazenados em arquivo JSON.
    Implementa hashing de senhas para segurança.
    """
    
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.users_file = self.base_dir / 'data' / 'users.json'
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Garante que o arquivo de usuários existe."""
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.users_file.exists():
            self.users_file.write_text(json.dumps([], indent=2))
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Gera hash SHA256 da senha."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def load_users(self) -> List[Dict]:
        """Carrega todos os usuários do arquivo JSON."""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
                # Normaliza campos novos para compatibilidade
                for u in users:
                    if 'must_change_password' not in u:
                        u['must_change_password'] = False
                return users
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _compute_role(self, user: Dict) -> str:
        """Resolve o papel do usuário (não persiste automaticamente)."""
        superadmin_username = getattr(settings, 'SUPERADMIN_USERNAME', '') or ''
        if superadmin_username and user.get('username') == superadmin_username:
            return 'SUPERADMIN'
        if user.get('position') == 'Administrador':
            return 'ADMIN'
        return 'USER'
    
    def save_users(self, users: List[Dict]) -> None:
        """Salva usuários no arquivo JSON."""
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Autentica um usuário com username e senha.
        Retorna os dados do usuário se autenticado, None caso contrário.
        """
        users = self.load_users()
        password_hash = self.hash_password(password)
        
        for user in users:
            if user.get('username') == username and user.get('password_hash') == password_hash:
                # Retorna usuário sem a senha
                user_copy = user.copy()
                user_copy.pop('password_hash', None)
                user_copy.pop('password_plain', None)
                user_copy['role'] = self._compute_role(user)
                user_copy['is_superadmin'] = (user_copy['role'] == 'SUPERADMIN')
                return user_copy
        
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Obtém usuário pelo username."""
        users = self.load_users()
        for user in users:
            if user.get('username') == username:
                user_copy = user.copy()
                user_copy.pop('password_hash', None)
                user_copy.pop('password_plain', None)
                user_copy['role'] = self._compute_role(user)
                user_copy['is_superadmin'] = (user_copy['role'] == 'SUPERADMIN')
                return user_copy
        return None

    def get_user_password_for_superadmin(self, username: str) -> Optional[str]:
        """Retorna a senha atual (texto) do usuário, se armazenada."""
        users = self.load_users()
        for user in users:
            if user.get('username') == username:
                return user.get('password_plain')
        return None
    
    def user_exists(self, username: str) -> bool:
        """Verifica se um usuário já existe."""
        return self.get_user_by_username(username) is not None
    
    def create_user(self, username: str, password: str, name: str,
                   position: str = 'Operador', must_change_password: bool = True) -> Dict:
        """
        Cria um novo usuário.
        
        Args:
            username: Nome de usuário único
            password: Senha em texto plano (será hasheada)
            name: Nome completo
            position: Cargo/posição do usuário
        
        Returns:
            Dados do usuário criado (sem senha)
        """
        if self.user_exists(username):
            raise ValueError(f"Usuário '{username}' já existe")
        
        users = self.load_users()
        
        new_user = {
            'id': len(users) + 1,
            'username': username,
            'password_hash': self.hash_password(password),
            # Atenção: armazenar senha em texto plano é sensível. Necessário para o caso de uso
            # solicitado (apenas SUPERADMIN pode visualizar). O acesso é bloqueado por permissão.
            'password_plain': password,
            'name': name,
            'position': position,
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'must_change_password': bool(must_change_password),
        }
        
        users.append(new_user)
        self.save_users(users)
        
        # Retorna sem a senha
        user_copy = new_user.copy()
        user_copy.pop('password_hash')
        user_copy.pop('password_plain', None)
        user_copy['role'] = self._compute_role(new_user)
        user_copy['is_superadmin'] = (user_copy['role'] == 'SUPERADMIN')
        return user_copy
    
    def update_last_login(self, username: str) -> None:
        """Atualiza o timestamp do último login."""
        users = self.load_users()
        for user in users:
            if user.get('username') == username:
                user['last_login'] = datetime.now().isoformat()
                break
        self.save_users(users)
    
    def update_user(self, username: str, **kwargs) -> Optional[Dict]:
        """
        Atualiza dados do usuário.
        Não permite alterar username ou password_hash diretamente.
        """
        users = self.load_users()
        
        for user in users:
            if user.get('username') == username:
                # Campos permitidos para atualização
                allowed_fields = {'name', 'position'}
                
                for key, value in kwargs.items():
                    if key in allowed_fields:
                        user[key] = value
                
                self.save_users(users)
                
                user_copy = user.copy()
                user_copy.pop('password_hash', None)
                user_copy.pop('password_plain', None)
                user_copy['role'] = self._compute_role(user)
                user_copy['is_superadmin'] = (user_copy['role'] == 'SUPERADMIN')
                return user_copy
        
        return None
    
    def delete_user(self, username: str) -> bool:
        """Deleta um usuário."""
        users = self.load_users()
        original_count = len(users)
        users = [u for u in users if u.get('username') != username]
        
        if len(users) < original_count:
            self.save_users(users)
            return True
        return False
    
    def list_all_users(self) -> List[Dict]:
        """Lista todos os usuários (sem senhas)."""
        users = self.load_users()
        safe_users = []
        for user in users:
            safe = {k: v for k, v in user.items() if k not in ('password_hash', 'password_plain')}
            safe['role'] = self._compute_role(user)
            safe_users.append(safe)
        return safe_users
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Altera a senha de um usuário."""
        users = self.load_users()
        old_password_hash = self.hash_password(old_password)
        new_password_hash = self.hash_password(new_password)
        
        for user in users:
            if user.get('username') == username:
                if user.get('password_hash') == old_password_hash:
                    user['password_hash'] = new_password_hash
                    user['password_plain'] = new_password
                    user['must_change_password'] = False
                    self.save_users(users)
                    return True
                return False
        
        return False

    def set_password_admin(self, username: str, new_password: str, force_user_reset: bool = True) -> bool:
        """Reseta a senha (sem exigir senha antiga). Uso restrito ao SUPERADMIN."""
        users = self.load_users()
        for user in users:
            if user.get('username') == username:
                user['password_hash'] = self.hash_password(new_password)
                user['password_plain'] = new_password
                if force_user_reset:
                    user['must_change_password'] = True
                self.save_users(users)
                return True
        return False

    def set_password_self(self, username: str, new_password: str) -> bool:
        """Define a senha do próprio usuário (sem exigir old_password) e libera acesso."""
        users = self.load_users()
        for user in users:
            if user.get('username') == username:
                user['password_hash'] = self.hash_password(new_password)
                user['password_plain'] = new_password
                user['must_change_password'] = False
                self.save_users(users)
                return True
        return False


# Instância global do gerenciador
user_manager = UserManager()
