from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    jsonify,
    current_app,
)
from . import blueprint

from flask_login import login_required, current_user
from app.decorators import enabled_required
from app.config import Config
from app import db, app

from .models import (
    PrintHubFilament,
    get_current_time,
    PrintHubPrinter,
    PrintHubEnergyCost,
)

from sqlalchemy.exc import IntegrityError
from datetime import datetime

config = Config()
print("PrintHub 0.0.0")


@blueprint.route("/printHub_index", methods=["GET"])
@enabled_required
# nur hier ist der Name gross!!
def PrintHub_index():
    app.logger.info("PrintHub page accessed")
    return render_template("PrintHub.html", user=current_user, config=config)


@blueprint.route("/printHub_filaments", methods=["GET", "POST"])
@login_required
@enabled_required
def printHub_filaments():
    """Filament-Verwaltung - Anzeigen und Hinzufügen"""

    if request.method == "POST":
        try:
            # Form-Daten extrahieren
            filament_type = request.form.get("filament_type", "").strip()
            name = request.form.get("filament_name", "").strip()
            manufacturer = request.form.get("filament_manufacturer", "").strip()
            weight = request.form.get("filament_weight", type=int)
            price = request.form.get("filament_price", type=float)
            notes = request.form.get("filament_notes", "").strip()

            # Validierung
            if not all([filament_type, name, manufacturer]) or not weight or not price:
                flash("Bitte füllen Sie alle Pflichtfelder aus!", "error")
                return redirect(url_for("PrintHub.printHub_filaments"))

            if weight <= 0 or price <= 0:
                flash("Gewicht und Preis müssen größer als 0 sein!", "error")
                return redirect(url_for("PrintHub.printHub_filaments"))

            if filament_type not in PrintHubFilament.get_filament_types():
                flash("Ungültiger Filament-Typ!", "error")
                return redirect(url_for("PrintHub.printHub_filaments"))

            # Neues Filament erstellen
            new_filament = PrintHubFilament(
                filament_type=filament_type,
                name=name,
                manufacturer=manufacturer,
                weight=weight,
                price=price,
                notes=notes if notes else None,
                created_by=current_user.username,
                created_at=get_current_time(),
                updated_at=get_current_time(),
            )

            # In Datenbank speichern
            db.session.add(new_filament)
            db.session.commit()

            flash(f'Filament "{name}" erfolgreich hinzugefügt!', "success")
            current_app.logger.info(
                f"User {current_user.username} added filament: {name}"
            )

        except IntegrityError as e:
            db.session.rollback()
            flash(
                "Fehler beim Speichern des Filaments. Bitte versuchen Sie es erneut.",
                "error",
            )
            current_app.logger.error(f"Database integrity error: {e}")

        except Exception as e:
            db.session.rollback()
            flash("Ein unerwarteter Fehler ist aufgetreten.", "error")
            current_app.logger.error(f"Unexpected error adding filament: {e}")

        return redirect(url_for("PrintHub.printHub_filaments"))

    # GET Request - Filamente laden
    try:
        # Suchparameter
        search_term = request.args.get("search", "").strip()
        filter_type = request.args.get("type", "").strip()

        # Filamente laden
        if search_term or filter_type:
            filaments = PrintHubFilament.search(
                username=current_user.username,
                search_term=search_term if search_term else None,
                filament_type=filter_type if filter_type else None,
            )
        else:
            filaments = PrintHubFilament.get_by_user(current_user.username)

        # Statistiken berechnen
        stats = {
            "total_filaments": len(filaments),
            "total_value": sum(float(f.price) for f in filaments),
            "total_weight": sum(f.weight for f in filaments),
            "types": {},
        }

        # Typ-Statistiken
        for filament in filaments:
            if filament.filament_type not in stats["types"]:
                stats["types"][filament.filament_type] = {
                    "count": 0,
                    "weight": 0,
                    "value": 0,
                }
            stats["types"][filament.filament_type]["count"] += 1
            stats["types"][filament.filament_type]["weight"] += filament.weight
            stats["types"][filament.filament_type]["value"] += float(filament.price)

        return render_template(
            "PrintHubFilaments.html",
            user=current_user,
            config=config,
            active_page="filaments",
            filaments=filaments,
            stats=stats,
            filament_types=PrintHubFilament.get_filament_types(),
            search_term=search_term,
            filter_type=filter_type,
        )

    except Exception as e:
        flash("Fehler beim Laden der Filamente.", "error")
        current_app.logger.error(f"Error loading filaments: {e}")
        return render_template(
            "PrintHubFilaments.html",
            user=current_user,
            config=config,
            active_page="filaments",
            filaments=[],
            stats={
                "total_filaments": 0,
                "total_value": 0,
                "total_weight": 0,
                "types": {},
            },
            filament_types=PrintHubFilament.get_filament_types(),
            search_term="",
            filter_type="",
        )


@blueprint.route("/filament/delete_filament/<int:filament_id>", methods=["POST"])
@enabled_required
def delete_filament(filament_id):
    """Filament löschen - nur eigene Filamente"""
    try:
        # Filament laden und prüfen ob es dem aktuellen Benutzer gehört
        filament = PrintHubFilament.query.filter_by(
            id=filament_id, created_by=current_user.username
        ).first()

        if not filament:
            flash(
                "Filament nicht gefunden oder Sie haben keine Berechtigung zum Löschen.",
                "error",
            )
            return redirect(url_for("PrintHub.printHub_filaments"))

        filament_name = filament.name
        filament_type = filament.filament_type

        # Filament löschen
        db.session.delete(filament)
        db.session.commit()

        flash(
            f'Filament "{filament_name}" ({filament_type}) erfolgreich gelöscht!',
            "success",
        )
        current_app.logger.info(
            f"User {current_user.username} deleted filament: {filament_name} ({filament_type})"
        )

    except Exception as e:
        db.session.rollback()
        flash("Fehler beim Löschen des Filaments.", "error")
        current_app.logger.error(f"Error deleting filament: {e}")

    return redirect(url_for("PrintHub.printHub_filaments"))


# API Endpoints
@blueprint.route("/api/filaments", methods=["GET"])
@enabled_required
def api_filaments():
    """API: Alle Filamente als JSON"""
    try:
        filaments = PrintHubFilament.get_by_user(current_user.username)
        return jsonify({"success": True, "data": [f.to_dict() for f in filaments]})
    except Exception as e:
        current_app.logger.error(f"Error in API filaments: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# Printer Seiten
@blueprint.route("/printHub_printers", methods=["GET", "POST"])
@enabled_required
def printHub_printers():
    """Drucker-Verwaltung - Ohne manuelle Rollbacks"""

    if request.method == "POST":
        try:
            # Form-Daten extrahieren
            name = request.form.get("printer_name", "").strip()
            brand = request.form.get("printer_brand", "").strip()
            machine_cost_per_hour = request.form.get(
                "machine_cost_per_hour", type=float
            )
            energy_consumption = request.form.get("energy_consumption", type=int)
            notes = request.form.get("printer_notes", "").strip()

            # Validierung
            if not all([name, brand]) or not machine_cost_per_hour:
                flash("Bitte füllen Sie alle Pflichtfelder aus!", "error")
                return redirect(url_for("PrintHub.printHub_printers"))

            if machine_cost_per_hour <= 0:
                flash("Maschinenkosten müssen größer als 0 sein!", "error")
                return redirect(url_for("PrintHub.printHub_printers"))

            # Neuen Drucker erstellen
            new_printer = PrintHubPrinter(
                name=name,
                brand=brand,
                machine_cost_per_hour=machine_cost_per_hour,
                energy_consumption=energy_consumption if energy_consumption else None,
                notes=notes if notes else None,
                created_by=current_user.username,
            )

            db.session.add(new_printer)
            print("Printer added to reset session")
            db.session.commit()
            print("Reset session commit successful!")

            flash(f'Drucker "{name}" erfolgreich hinzugefügt!', "success")
            current_app.logger.info(
                f"User {current_user.username} added printer: {name}"
            )

        except Exception as e:
            flash("Ein unerwarteter Fehler ist aufgetreten.", "error")
            current_app.logger.error(f"Error with reset session: {e}")
            print(f"Error with reset session: {e}")

        return redirect(url_for("PrintHub.printHub_printers"))

    # GET Request - Drucker laden
    try:
        search_term = request.args.get("search", "").strip()

        if search_term:
            printers = PrintHubPrinter.search(
                username=current_user.username, search_term=search_term
            )
        else:
            printers = PrintHubPrinter.get_by_user(current_user.username)

        stats = {
            "total_printers": len(printers),
            "total_daily_cost": sum(p.daily_machine_cost for p in printers),
            "total_hourly_cost": sum(float(p.machine_cost_per_hour) for p in printers),
        }

        return render_template(
            "PrintHubPrinters.html",
            user=current_user,
            config=config,
            active_page="printers",
            printers=printers,
            stats=stats,
            printer_brands=PrintHubPrinter.get_common_brands(),
            search_term=search_term,
        )

    except Exception as e:
        flash("Fehler beim Laden der Drucker.", "error")
        current_app.logger.error(f"Error loading printers: {e}")
        return render_template(
            "PrintHubPrinters.html",
            user=current_user,
            config=config,
            active_page="printers",
            printers=[],
            stats={"total_printers": 0, "total_daily_cost": 0, "total_hourly_cost": 0},
            printer_brands=PrintHubPrinter.get_common_brands(),
            search_term="",
        )


@blueprint.route("/printer/delete_printer/<int:printer_id>", methods=["POST"])
@enabled_required
def delete_printer(printer_id):
    """Drucker löschen - nur eigene Drucker"""
    try:
        # Drucker laden und prüfen ob er dem aktuellen Benutzer gehört
        printer = PrintHubPrinter.query.filter_by(
            id=printer_id, created_by=current_user.username
        ).first()

        if not printer:
            flash(
                "Drucker nicht gefunden oder Sie haben keine Berechtigung zum Löschen.",
                "error",
            )
            return redirect(url_for("PrintHub.printHub_printers"))

        printer_name = printer.name
        printer_brand = printer.brand

        # Drucker löschen
        db.session.delete(printer)
        db.session.commit()

        flash(
            f'Drucker "{printer_name}" ({printer_brand}) erfolgreich gelöscht!',
            "success",
        )
        current_app.logger.info(
            f"User {current_user.username} deleted printer: {printer_name} ({printer_brand})"
        )

    except Exception as e:
        db.session.rollback()
        flash("Fehler beim Löschen des Druckers.", "error")
        current_app.logger.error(f"Error deleting printer: {e}")

    return redirect(url_for("PrintHub.printHub_printers"))


# API Endpoints
@blueprint.route("/api/printers", methods=["GET"])
@login_required
@enabled_required
def api_printers():
    """API: Alle Drucker als JSON"""
    try:
        printers = PrintHubPrinter.get_by_user(current_user.username)
        return jsonify({"success": True, "data": [p.to_dict() for p in printers]})
    except Exception as e:
        current_app.logger.error(f"Error in API printers: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# Engergikosten
@blueprint.route("/printHub_energy_costs", methods=["GET", "POST"])
@enabled_required
def printHub_energy_costs():
    """Energiekosten-Verwaltung - Anzeigen und Hinzufügen"""

    if request.method == "POST":
        try:
            # Form-Daten extrahieren
            name = request.form.get("energy_name", "").strip()
            provider = request.form.get("energy_provider", "").strip()
            cost_per_kwh = request.form.get("cost_per_kwh", type=float)
            base_fee_monthly = request.form.get("base_fee_monthly", type=float)
            tariff_type = request.form.get("tariff_type", "").strip()
            valid_from = request.form.get("valid_from", "")
            valid_until = request.form.get("valid_until", "")
            night_rate = request.form.get("night_rate", type=float)
            is_active = request.form.get("is_active") == "on"
            notes = request.form.get("energy_notes", "").strip()

            # Validierung
            if not all([name, provider]) or not cost_per_kwh:
                flash("Bitte füllen Sie alle Pflichtfelder aus!", "error")
                return redirect(url_for("PrintHub.printHub_energy_costs"))

            if cost_per_kwh <= 0:
                flash("Kosten pro kWh müssen größer als 0 sein!", "error")
                return redirect(url_for("PrintHub.printHub_energy_costs"))

            if base_fee_monthly and base_fee_monthly < 0:
                flash("Grundgebühr kann nicht negativ sein!", "error")
                return redirect(url_for("PrintHub.printHub_energy_costs"))

            # Datum-Konvertierung
            valid_from_date = None
            valid_until_date = None

            if valid_from:
                try:
                    valid_from_date = datetime.strptime(valid_from, "%Y-%m-%d").date()
                except ValueError:
                    flash("Ungültiges 'Gültig von' Datum!", "error")
                    return redirect(url_for("PrintHub.printHub_energy_costs"))

            if valid_until:
                try:
                    valid_until_date = datetime.strptime(valid_until, "%Y-%m-%d").date()
                    if valid_from_date and valid_until_date <= valid_from_date:
                        flash("'Gültig bis' muss nach 'Gültig von' liegen!", "error")
                        return redirect(url_for("PrintHub.printHub_energy_costs"))
                except ValueError:
                    flash("Ungültiges 'Gültig bis' Datum!", "error")
                    return redirect(url_for("PrintHub.printHub_energy_costs"))

            # Neue Energiekosten erstellen
            new_energy_cost = PrintHubEnergyCost(
                name=name,
                provider=provider,
                cost_per_kwh=cost_per_kwh,
                base_fee_monthly=base_fee_monthly if base_fee_monthly else None,
                tariff_type=tariff_type if tariff_type else None,
                valid_from=valid_from_date,
                valid_until=valid_until_date,
                night_rate=night_rate if night_rate else None,
                is_active=is_active,
                notes=notes if notes else None,
                created_by=current_user.username,
                created_at=get_current_time(),
                updated_at=get_current_time(),
            )

            # In Datenbank speichern
            db.session.add(new_energy_cost)
            db.session.commit()

            flash(f'Energietarif "{name}" erfolgreich hinzugefügt!', "success")
            current_app.logger.info(
                f"User {current_user.username} added energy cost: {name}"
            )

        except Exception as e:
            flash("Ein unerwarteter Fehler ist aufgetreten.", "error")
            current_app.logger.error(f"Unexpected error adding energy cost: {e}")

        return redirect(url_for("PrintHub.printHub_energy_costs"))

    # GET Request - Energiekosten laden
    try:
        # Suchparameter
        search_term = request.args.get("search", "").strip()
        filter_provider = request.args.get("provider", "").strip()
        show_inactive = request.args.get("show_inactive", "").strip() == "true"

        # Energiekosten laden
        if search_term or filter_provider:
            energy_costs = PrintHubEnergyCost.search(
                username=current_user.username,
                search_term=search_term if search_term else None,
                provider=filter_provider if filter_provider else None,
                include_inactive=show_inactive,
            )
        else:
            energy_costs = PrintHubEnergyCost.get_by_user(
                current_user.username, include_inactive=show_inactive
            )

        # Statistiken berechnen
        active_costs = [ec for ec in energy_costs if ec.is_active]

        stats = {
            "total_tariffs": len(energy_costs),
            "active_tariffs": len(active_costs),
            "avg_cost_per_kwh": (
                sum(float(ec.cost_per_kwh) for ec in active_costs) / len(active_costs)
                if active_costs
                else 0
            ),
            "cheapest_tariff": min(
                active_costs, key=lambda x: x.cost_per_kwh, default=None
            ),
            "most_expensive_tariff": max(
                active_costs, key=lambda x: x.cost_per_kwh, default=None
            ),
            "providers": list(set(ec.provider for ec in energy_costs)),
            "total_monthly_base_fees": sum(
                float(ec.base_fee_monthly or 0) for ec in active_costs
            ),
        }

        return render_template(
            "PrintHubEnergyCosts.html",
            user=current_user,
            config=config,
            active_page="energy_costs",
            energy_costs=energy_costs,
            stats=stats,
            tariff_types=PrintHubEnergyCost.get_tariff_types(),
            providers=stats["providers"],
            search_term=search_term,
            filter_provider=filter_provider,
            show_inactive=show_inactive,
        )

    except Exception as e:
        flash("Fehler beim Laden der Energiekosten.", "error")
        current_app.logger.error(f"Error loading energy costs: {e}")
        return render_template(
            "PrintHubEnergyCosts.html",
            user=current_user,
            config=config,
            active_page="energy_costs",
            energy_costs=[],
            stats={
                "total_tariffs": 0,
                "active_tariffs": 0,
                "avg_cost_per_kwh": 0,
                "cheapest_tariff": None,
                "most_expensive_tariff": None,
                "providers": [],
                "total_monthly_base_fees": 0,
            },
            tariff_types=PrintHubEnergyCost.get_tariff_types(),
            providers=[],
            search_term="",
            filter_provider="",
            show_inactive=False,
        )


# Zu Ihrer routes.py hinzufügen:


@blueprint.route(
    "/energy_cost/delete_energy_cost/<int:energy_cost_id>", methods=["POST"]
)
@enabled_required
def delete_energy_cost(energy_cost_id):
    """Energiekosten löschen - nur eigene Energiekosten"""
    try:
        # Energiekosten laden und prüfen ob sie dem aktuellen Benutzer gehören
        energy_cost = PrintHubEnergyCost.query.filter_by(
            id=energy_cost_id, created_by=current_user.username
        ).first()

        if not energy_cost:
            flash(
                "Energietarif nicht gefunden oder Sie haben keine Berechtigung zum Löschen.",
                "error",
            )
            return redirect(url_for("PrintHub.printHub_energy_costs"))

        energy_cost_name = energy_cost.name
        energy_cost_provider = energy_cost.provider

        # Energiekosten löschen
        db.session.delete(energy_cost)
        db.session.commit()

        flash(
            f'Energietarif "{energy_cost_name}" ({energy_cost_provider}) erfolgreich gelöscht!',
            "success",
        )
        current_app.logger.info(
            f"User {current_user.username} deleted energy cost: {energy_cost_name} ({energy_cost_provider})"
        )

    except Exception as e:
        flash("Fehler beim Löschen des Energietarifs.", "error")
        current_app.logger.error(f"Error deleting energy cost: {e}")

    return redirect(url_for("PrintHub.printHub_energy_costs"))
