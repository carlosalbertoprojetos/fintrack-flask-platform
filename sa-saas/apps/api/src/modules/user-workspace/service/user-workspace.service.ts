import bcrypt from "bcryptjs";
import { prisma } from "../../../core/prisma/client.js";
import { HttpError } from "../../../core/http/error-handler.js";
import { signToken } from "../../../core/auth/jwt.js";
import type { LoginInput, RegisterUserInput } from "../domain/types.js";

export class UserWorkspaceService {
  async register(input: RegisterUserInput) {
    const existing = await prisma.user.findUnique({ where: { email: input.email.toLowerCase() } });
    if (existing) {
      throw new HttpError(409, "Email already in use");
    }

    const passwordHash = await bcrypt.hash(input.password, 12);

    const user = await prisma.user.create({
      data: {
        email: input.email.toLowerCase(),
        passwordHash,
        fullName: input.fullName,
        workspaces: {
          create: {
            name: input.workspaceName
          }
        }
      },
      include: {
        workspaces: true
      }
    });

    const workspace = user.workspaces[0];
    const token = signToken({ userId: user.id, workspaceId: workspace.id });

    return {
      token,
      user: {
        id: user.id,
        email: user.email,
        fullName: user.fullName
      },
      workspace: {
        id: workspace.id,
        name: workspace.name
      }
    };
  }

  async login(input: LoginInput) {
    const user = await prisma.user.findUnique({
      where: { email: input.email.toLowerCase() },
      include: { workspaces: true }
    });

    if (!user) {
      throw new HttpError(401, "Invalid credentials");
    }

    const isValidPassword = await bcrypt.compare(input.password, user.passwordHash);
    if (!isValidPassword) {
      throw new HttpError(401, "Invalid credentials");
    }

    const workspace = user.workspaces[0];
    if (!workspace) {
      throw new HttpError(400, "No workspace linked to user");
    }

    const token = signToken({ userId: user.id, workspaceId: workspace.id });

    return {
      token,
      user: {
        id: user.id,
        email: user.email,
        fullName: user.fullName
      },
      workspace: {
        id: workspace.id,
        name: workspace.name
      }
    };
  }

  async me(userId: string, workspaceId: string) {
    const user = await prisma.user.findUnique({ where: { id: userId } });
    const workspace = await prisma.workspace.findUnique({ where: { id: workspaceId } });

    if (!user || !workspace) {
      throw new HttpError(404, "User or workspace not found");
    }

    return {
      user: {
        id: user.id,
        email: user.email,
        fullName: user.fullName
      },
      workspace: {
        id: workspace.id,
        name: workspace.name
      }
    };
  }
}
