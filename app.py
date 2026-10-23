        }
        status = request.form.get("status")

        if status not in allowed:
            abort(400)

        complaint.status = status
        complaint.updated_at = datetime.utcnow()
        db.session.commit()

        flash("Complaint status updated.", "success")
        return redirect(
            url_for("complaint_detail", complaint_id=complaint.id)
        )

    @app.route("/complaints/<int:complaint_id>/fir", methods=["POST"])
    @role_required("officer", "admin")
    def create_fir(complaint_id):
        complaint = db.get_or_404(Complaint, complaint_id)

        if complaint.fir:
            flash(
                "An FIR record already exists for this complaint.",
                "info",
            )
            return redirect(
                url_for("complaint_detail", complaint_id=complaint.id)
            )

        sections = request.form.get("sections", "").strip()
        notes = request.form.get("officer_notes", "").strip()

        fir = FIR(
            complaint_id=complaint.id,
            fir_number=(
                f"DEMO-FIR-{datetime.now().year}-{complaint.id:05d}"
            ),
            sections=sections or None,
            officer_notes=notes or None,
            registered_by=current_user.id,
        )
        db.session.add(fir)
        complaint.status = "Investigation"
        complaint.updated_at = datetime.utcnow()
        db.session.commit()

        flash(
            "Demonstration FIR record created. This is not an official police FIR number.",
            "success",
        )
        return redirect(
            url_for("complaint_detail", complaint_id=complaint.id)
        )

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.cli.command("init-db")
    def init_db():
        """Create database tables."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("create-officer")
    @click.option("--name", prompt=True, help="Officer display name")
    @click.option("--email", prompt=True, help="Officer email address")
    @click.password_option(confirmation_prompt=True)
    def create_officer(name, email, password):
        """Create an officer account for local demonstration."""
        email = email.strip().lower()

        if User.query.filter_by(email=email).first():
            click.echo("A user with that email already exists.")
            return

        user = User(
            name=name.strip(),
            email=email,
            password_hash=generate_password_hash(password),
            role="officer",
        )
        db.session.add(user)
        db.session.commit()
        click.echo(f"Officer account created for {email}.")

    return app


app = create_app()

# Ensure tables are created when the app is imported by Gunicorn on Render.
# This fixes missing-table errors for a fresh SQLite database.
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )
